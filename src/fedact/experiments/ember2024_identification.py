from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass

import numpy as np
import torch
from numpy.typing import NDArray

from fedact.certification.actions import projector_from_basis
from fedact.certification.certificate import ClientConstraint
from fedact.certification.client_procedure import (
    bootstrap_malicious_sampling_term,
    bootstrap_subspace_estimation_term,
    control_span_violation_term,
    malicious_transition_covariance,
    private_transition_term_single_client,
    select_stable_nuisance_rank,
)
from fedact.certification.dynamics import AbstentionReason
from fedact.certification.uncertainty import client_radius, regularized_covariance
from fedact.config.models import StrictModel
from fedact.data.ember2024 import (
    EmberRawRecord,
    LoadedEmberDataset,
    control_transition_replicates,
    load_ember2024_records,
    malicious_transition_displacement,
    validate_ember_dataset,
    windowed_malicious_features,
    year_month_to_calendar_month,
)
from fedact.data.splits import CalendarMonth, calendar_month, transition_windows
from fedact.domain.types import (
    EigengapRatio,
    EvaluationCount,
    FamilyName,
    RankDimension,
    ScientificOutcome,
    UncertaintyRadius,
    ValidationFlag,
    WindowSpanMonths,
)
from fedact.experiments.registry import ExperimentRuntime
from fedact.learning.representation import (
    DEFAULT_ENCODER_HIDDEN_DIMENSIONS,
    EMBEDDING_DIMENSION,
    RepresentationDataset,
    RepresentationEncoder,
    TrainingObservation,
    train_representation_encoder,
)

LOGGER = logging.getLogger(__name__)

FloatArray = NDArray[np.float64]
_SINGLE_CORPUS_LEVEL_CLIENT_COUNT = 1
_ALPHA_ALLOCATION_DENOMINATOR_FACTOR = 2.0
_EVIDENCE_JSON_INDENT_SPACES = 2


@dataclass(frozen=True)
class ClientConstraintFit:
    constraint: ClientConstraint
    selected_rank: RankDimension
    eigengap_ratio: EigengapRatio
    beta: UncertaintyRadius
    sampling_term: UncertaintyRadius
    subspace_term: UncertaintyRadius
    control_span_term: UncertaintyRadius
    private_term: UncertaintyRadius


def fit_ember2024_client_constraint(
    application: ExperimentRuntime,
    cohort_records: tuple[EmberRawRecord, ...],
    cohort_features: FloatArray,
    all_records: tuple[EmberRawRecord, ...],
    all_features: FloatArray,
    endpoint: CalendarMonth,
    historical_endpoints: tuple[CalendarMonth, ...],
    earlier_malicious_endpoints: tuple[CalendarMonth, ...],
) -> ClientConstraintFit | AbstentionReason:
    config = application.configuration.values
    transition_interval_months: WindowSpanMonths = config.temporal.transition_interval_months
    records, features = cohort_records, cohort_features

    malicious = malicious_transition_displacement(
        records, features, endpoint, transition_interval_months
    )
    if (
        malicious is None
        or malicious.support_before < config.identification.minimum_support_per_class
        or malicious.support_after < config.identification.minimum_support_per_class
    ):
        return AbstentionReason.ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT

    replicates = control_transition_replicates(
        all_records, all_features, historical_endpoints, transition_interval_months
    )
    if len(replicates) < config.identification.minimum_control_transition_replicates:
        return AbstentionReason.ABSTAIN_NO_USABLE_CONTROL

    replicate_displacements = [replicate.displacement for replicate in replicates]
    replicate_supports = [
        (replicate.support_before, replicate.support_after) for replicate in replicates
    ]
    dimension = features.shape[1]

    rank_selection = select_stable_nuisance_rank(
        replicate_displacements=replicate_displacements,
        replicate_supports=replicate_supports,
        dimension=dimension,
        configured_maximum_rank=config.identification.nuisance_rank.maximum,
        eigengap_requirement=config.identification.eigengap_ratio.default_without_nested_calibration,
        rank_clip_epsilon_relative=config.numerical.rank_clip_epsilon_relative,
        scale_standardization_floor=config.numerical.scale_standardization_floor,
        bootstrap_resamples=config.identification.nuisance_rank.bootstrap_resamples,
        minimum_bootstrap_stability_fraction=(
            config.identification.nuisance_rank.minimum_bootstrap_stability_fraction
        ),
        seed=config.seeds.calibration[0],
    )
    if rank_selection.eigengap_ratio < 1.0:
        return AbstentionReason.ABSTAIN_WEAK_EIGENGAP
    if not rank_selection.is_stable:
        return AbstentionReason.ABSTAIN_UNSTABLE_NUISANCE_RANK

    projector = projector_from_basis(rank_selection.subspace)

    window_minus, window_plus = windowed_malicious_features(
        records, features, endpoint, transition_interval_months
    )

    malicious_covariance_raw = malicious_transition_covariance(window_minus, window_plus)
    malicious_covariance = regularized_covariance(
        malicious_covariance_raw,
        coefficient=config.identification.covariance_regularization.primary_c,
        floor=config.numerical.scale_standardization_floor,
    )
    projected_malicious_covariance = projector @ malicious_covariance @ projector.T
    projected_malicious_covariance = regularized_covariance(
        projected_malicious_covariance,
        coefficient=config.identification.covariance_regularization.primary_c,
        floor=config.numerical.scale_standardization_floor,
    )
    smallest_malicious_eigenvalue = float(np.linalg.eigvalsh(projected_malicious_covariance).min())

    coverage = config.identification.target_coverage.primary
    alpha = (1.0 - coverage) / (
        _ALPHA_ALLOCATION_DENOMINATOR_FACTOR * _SINGLE_CORPUS_LEVEL_CLIENT_COUNT
    )

    sampling_term = bootstrap_malicious_sampling_term(
        window_minus,
        window_plus,
        malicious.displacement,
        projector,
        projected_malicious_covariance,
        alpha,
        config.identification.uncertainty.bootstrap_resamples,
        config.seeds.calibration[0],
    )
    subspace_term = bootstrap_subspace_estimation_term(
        replicate_displacements,
        replicate_supports,
        rank_selection.selected_rank,
        projector,
        alpha,
        config.identification.nuisance_rank.bootstrap_resamples,
        config.seeds.calibration[0],
        smallest_malicious_eigenvalue,
    )
    control_span_term = control_span_violation_term(
        replicate_displacements,
        replicate_supports,
        rank_selection.selected_rank,
        config.identification.control_span_violation.primary_alpha,
        smallest_malicious_eigenvalue,
    )

    earlier_transitions: list[FloatArray] = []
    for earlier_endpoint in earlier_malicious_endpoints:
        earlier = malicious_transition_displacement(
            records, features, earlier_endpoint, transition_interval_months
        )
        if (
            earlier is not None
            and earlier.support_before >= config.identification.minimum_support_per_class
            and earlier.support_after >= config.identification.minimum_support_per_class
        ):
            earlier_transitions.append(earlier.displacement)
    if (
        len(earlier_transitions)
        < config.identification.private_contamination.minimum_history_residuals
    ):
        return AbstentionReason.ABSTAIN_INSUFFICIENT_PRIVATE_ALLOWANCE_HISTORY
    private_term = private_transition_term_single_client(
        earlier_transitions,
        projector,
        config.identification.private_contamination.primary_alpha,
        smallest_malicious_eigenvalue,
        config.numerical.rank_clip_epsilon_relative,
        config.identification.nuisance_rank.bootstrap_resamples,
    )
    if private_term is None:
        return AbstentionReason.ABSTAIN_INSUFFICIENT_PRIVATE_ALLOWANCE_HISTORY

    beta = client_radius(sampling_term, subspace_term, control_span_term, private_term)
    constraint = ClientConstraint(
        client_index=0,
        uncertainty_radius=beta,
        beta=beta,
        subspace=rank_selection.subspace,
        projector=projector,
        covariance=projected_malicious_covariance,
    )
    LOGGER.info(
        "ember2024 client constraint fitted endpoint=%s rank=%s eigengap=%.4f beta=%.6f "
        "sampling=%.6f subspace=%.6f control_span=%.6f private=%.6f",
        endpoint,
        rank_selection.selected_rank,
        rank_selection.eigengap_ratio,
        beta,
        sampling_term,
        subspace_term,
        control_span_term,
        private_term,
    )
    return ClientConstraintFit(
        constraint=constraint,
        selected_rank=rank_selection.selected_rank,
        eigengap_ratio=rank_selection.eigengap_ratio,
        beta=beta,
        sampling_term=sampling_term,
        subspace_term=subspace_term,
        control_span_term=control_span_term,
        private_term=private_term,
    )


def _dominant_malicious_family_cohort(
    records: tuple[EmberRawRecord, ...],
) -> FamilyName | None:
    counts = Counter(
        record.family for record in records if record.label is True and record.family is not None
    )
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def _cohort_has_sufficient_malicious_support(
    cohort_records: tuple[EmberRawRecord, ...],
    endpoint: CalendarMonth,
    transition_interval_months: WindowSpanMonths,
    minimum_support_per_class: int,
) -> bool:
    windows = transition_windows(endpoint, transition_interval_months)
    before_count = 0
    after_count = 0
    for record in cohort_records:
        if record.label is not True:
            continue
        month = year_month_to_calendar_month(record.year_month)
        if windows.before_window_start_inclusive <= month < windows.before_window_end_exclusive:
            before_count += 1
        elif windows.after_window_start_inclusive <= month < windows.after_window_end_exclusive:
            after_count += 1
    return before_count >= minimum_support_per_class and after_count >= minimum_support_per_class


def _train_cutoff_representation_encoder(
    application: ExperimentRuntime,
    records: tuple[EmberRawRecord, ...],
    features: FloatArray,
    endpoint: CalendarMonth,
) -> RepresentationEncoder | None:
    config = application.configuration.values
    months = np.fromiter(
        (int(year_month_to_calendar_month(record.year_month)) for record in records),
        dtype=np.int64,
        count=len(records),
    )
    auditable = np.fromiter(
        (record.label is not None for record in records),
        dtype=bool,
        count=len(records),
    )
    cutoff_safe = auditable & (months < endpoint)
    if not np.any(cutoff_safe):
        return None
    safe_months = months[cutoff_safe]
    safe_records = tuple(record for record, keep in zip(records, cutoff_safe, strict=True) if keep)
    safe_features = features[cutoff_safe]
    validation_month = int(safe_months.max())
    training_indices = safe_months < validation_month
    validation_indices = safe_months == validation_month
    if not np.any(training_indices) or not np.any(validation_indices):
        return None

    def _observations(mask: NDArray[np.bool_]) -> tuple[TrainingObservation, ...]:
        return tuple(
            TrainingObservation(
                sample_id=record.sample_hash,
                features=torch.tensor(feature, dtype=torch.float32),
                month_index=int(month),
                label=bool(record.label),
            )
            for record, feature, month, keep in zip(
                safe_records, safe_features, safe_months, mask, strict=True
            )
            if keep
        )

    training = _observations(training_indices)
    validation = _observations(validation_indices)
    encoder, selection = train_representation_encoder(
        RepresentationDataset(training),
        RepresentationDataset(validation),
        features.shape[1],
        DEFAULT_ENCODER_HIDDEN_DIMENSIONS,
        EMBEDDING_DIMENSION,
        config.training.maximum_epochs,
        config.training.batch_size,
        config.training.initial_learning_rate,
        0.0,
        config.seeds.representation[0],
        config.numerical.projection_tie_tolerance,
    )
    LOGGER.info(
        "ember2024 cutoff representation encoder trained endpoint=%s rows=%s selected_epoch=%s",
        endpoint,
        len(training) + len(validation),
        selection.selected_epoch,
    )
    return encoder


def _embed_features(encoder: RepresentationEncoder, features: FloatArray) -> FloatArray:
    with torch.no_grad():
        embedded = encoder(torch.tensor(features, dtype=torch.float32))
    return embedded.numpy().astype(np.float64)


class _Ember2024IdentificationCutoffRecord(StrictModel):
    cutoff: CalendarMonth
    cohort: FamilyName
    fitted: ValidationFlag
    abstention_reason: AbstentionReason | None = None
    selected_rank: RankDimension | None = None
    eigengap_ratio: EigengapRatio | None = None
    beta: UncertaintyRadius | None = None


class _Ember2024IdentificationDiagnosticsArtifact(StrictModel):
    cohort: FamilyName
    cutoffs: list[_Ember2024IdentificationCutoffRecord]


@dataclass(frozen=True)
class Ember2024IdentificationDiagnosticsReport:
    cohort: FamilyName | None
    cutoffs_evaluated: EvaluationCount
    cutoffs_fitted: EvaluationCount
    scientific_outcome: ScientificOutcome


def run_ember2024_identification_diagnostics(
    application: ExperimentRuntime,
) -> Ember2024IdentificationDiagnosticsReport:
    raw_root = application.repository_root / "data" / "raw" / "EMBER2024"
    if not raw_root.is_dir():
        LOGGER.warning("ember2024 identification diagnostics has no release at %s", raw_root)
        return Ember2024IdentificationDiagnosticsReport(
            None, 0, 0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    config = application.configuration.values
    loaded: LoadedEmberDataset = load_ember2024_records(raw_root)
    validate_ember_dataset(loaded)
    if not loaded.records:
        return Ember2024IdentificationDiagnosticsReport(
            None, 0, 0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )

    cohort = _dominant_malicious_family_cohort(loaded.records)
    if cohort is None:
        LOGGER.warning("ember2024 identification diagnostics found no family-labeled cohort")
        return Ember2024IdentificationDiagnosticsReport(
            None, 0, 0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    cohort_mask = np.fromiter(
        (record.family == cohort for record in loaded.records),
        dtype=bool,
        count=len(loaded.records),
    )
    cohort_records = tuple(
        record for record, keep in zip(loaded.records, cohort_mask, strict=True) if keep
    )
    months = np.fromiter(
        (int(year_month_to_calendar_month(record.year_month)) for record in cohort_records),
        dtype=np.int64,
        count=len(cohort_records),
    )
    history = config.temporal.historical_training_window_months
    step = config.temporal.cutoff_step_months
    horizon = config.temporal.primary_confirmatory_horizon_months
    month_min, month_max = int(months.min()), int(months.max())

    records_list: list[_Ember2024IdentificationCutoffRecord] = []
    fitted = 0
    for endpoint_ordinal in range(month_min + 1, month_max - horizon + 1, max(step, 1)):
        endpoint = calendar_month(endpoint_ordinal)
        historical_endpoints = tuple(
            calendar_month(candidate)
            for candidate in range(max(month_min, endpoint_ordinal - history), endpoint_ordinal)
        )
        earlier_malicious_endpoints = tuple(
            calendar_month(candidate)
            for candidate in range(max(month_min, endpoint_ordinal - history), endpoint_ordinal - 1)
        )
        if not _cohort_has_sufficient_malicious_support(
            cohort_records,
            endpoint,
            config.temporal.transition_interval_months,
            config.identification.minimum_support_per_class,
        ):
            records_list.append(
                _Ember2024IdentificationCutoffRecord(
                    cutoff=endpoint,
                    cohort=cohort,
                    fitted=False,
                    abstention_reason=AbstentionReason.ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT,
                )
            )
            continue
        encoder = _train_cutoff_representation_encoder(
            application, loaded.records, loaded.features, endpoint
        )
        if encoder is None:
            records_list.append(
                _Ember2024IdentificationCutoffRecord(
                    cutoff=endpoint,
                    cohort=cohort,
                    fitted=False,
                    abstention_reason=AbstentionReason.ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT,
                )
            )
            continue
        embedded_features = _embed_features(encoder, loaded.features)
        embedded_cohort_features = embedded_features[cohort_mask]
        fit = fit_ember2024_client_constraint(
            application,
            cohort_records,
            embedded_cohort_features,
            loaded.records,
            embedded_features,
            endpoint,
            historical_endpoints,
            earlier_malicious_endpoints,
        )
        if isinstance(fit, ClientConstraintFit):
            fitted += 1
            records_list.append(
                _Ember2024IdentificationCutoffRecord(
                    cutoff=endpoint,
                    cohort=cohort,
                    fitted=True,
                    selected_rank=fit.selected_rank,
                    eigengap_ratio=fit.eigengap_ratio,
                    beta=fit.beta,
                )
            )
        else:
            records_list.append(
                _Ember2024IdentificationCutoffRecord(
                    cutoff=endpoint,
                    cohort=cohort,
                    fitted=False,
                    abstention_reason=fit,
                )
            )

    destination = (
        application.repository_root
        / config.workspace.directories.experiments
        / "prospective-evaluation"
        / "ember2024-identification-diagnostics.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        _Ember2024IdentificationDiagnosticsArtifact(
            cohort=cohort, cutoffs=records_list
        ).model_dump_json(indent=_EVIDENCE_JSON_INDENT_SPACES),
        encoding="utf-8",
    )
    return Ember2024IdentificationDiagnosticsReport(
        cohort=cohort,
        cutoffs_evaluated=len(records_list),
        cutoffs_fitted=fitted,
        scientific_outcome=(
            ScientificOutcome.PASS if fitted > 0 else ScientificOutcome.INSUFFICIENT_EVIDENCE
        ),
    )
