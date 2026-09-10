from __future__ import annotations

import logging
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

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
from fedact.data.lamda import (
    ControlTransitionReplicate,
    LabelDerivationRule,
    LamdaRawRecord,
    LoadedLamdaDataset,
    audited_label,
    control_transition_replicates,
    filter_low_variance_features,
    label_derivation_rule,
    load_lamda_records,
    malicious_transition_displacement,
    validate_lamda_dataset,
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
    SensitivityMultiplier,
    UncertaintyRadius,
    ValidationFlag,
    VarianceThreshold,
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


def fit_lamda_client_constraint(
    application: ExperimentRuntime,
    cohort_records: tuple[LamdaRawRecord, ...],
    cohort_features: FloatArray,
    all_records: tuple[LamdaRawRecord, ...],
    all_features: FloatArray,
    rule: LabelDerivationRule,
    endpoint: CalendarMonth,
    historical_endpoints: tuple[CalendarMonth, ...],
    earlier_malicious_endpoints: tuple[CalendarMonth, ...],
) -> ClientConstraintFit | AbstentionReason:
    config = application.configuration.values
    transition_interval_months: WindowSpanMonths = config.temporal.transition_interval_months
    records, features = cohort_records, cohort_features

    malicious = malicious_transition_displacement(
        records, features, rule, endpoint, transition_interval_months
    )
    if (
        malicious is None
        or malicious.support_before < config.identification.minimum_support_per_class
        or malicious.support_after < config.identification.minimum_support_per_class
    ):
        return AbstentionReason.ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT

    replicates = control_transition_replicates(
        all_records, all_features, rule, historical_endpoints, transition_interval_months
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
        records, features, rule, endpoint, transition_interval_months
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
            records, features, rule, earlier_endpoint, transition_interval_months
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
        "lamda client constraint fitted endpoint=%s rank=%s eigengap=%.4f beta=%.6f "
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
    )


class _IdentificationCutoffRecord(StrictModel):
    cutoff: CalendarMonth
    cohort: FamilyName
    fitted: ValidationFlag
    abstention_reason: AbstentionReason | None = None
    selected_rank: RankDimension | None = None
    eigengap_ratio: EigengapRatio | None = None
    beta: UncertaintyRadius | None = None


class _IdentificationDiagnosticsArtifact(StrictModel):
    cohort: FamilyName
    cutoffs: list[_IdentificationCutoffRecord]


@dataclass(frozen=True)
class IdentificationDiagnosticsReport:
    cohort: FamilyName | None
    cutoffs_evaluated: EvaluationCount
    cutoffs_fitted: EvaluationCount
    scientific_outcome: ScientificOutcome


def _load_variance_filtered_lamda_dataset(
    raw_root: Path, variance_threshold: VarianceThreshold
) -> LoadedLamdaDataset:
    loaded = load_lamda_records(raw_root)
    validate_lamda_dataset(loaded)
    filtered_features = filter_low_variance_features(loaded.features, variance_threshold)
    return LoadedLamdaDataset(records=loaded.records, features=filtered_features)


def _train_cutoff_representation_encoder(
    application: ExperimentRuntime,
    records: tuple[LamdaRawRecord, ...],
    features: FloatArray,
    rule: LabelDerivationRule,
    endpoint: CalendarMonth,
) -> RepresentationEncoder | None:
    config = application.configuration.values
    months = np.fromiter(
        (int(year_month_to_calendar_month(record.year_month)) for record in records),
        dtype=np.int64,
        count=len(records),
    )
    auditable = np.fromiter(
        (audited_label(rule, record).binary_label is not None for record in records),
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
                label=bool(audited_label(rule, record).binary_label),
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
        "cutoff representation encoder trained endpoint=%s rows=%s selected_epoch=%s",
        endpoint,
        len(training) + len(validation),
        selection.selected_epoch,
    )
    return encoder


def _embed_features(encoder: RepresentationEncoder, features: FloatArray) -> FloatArray:
    with torch.no_grad():
        embedded = encoder(torch.tensor(features, dtype=torch.float32))
    return embedded.detach().cpu().numpy().astype(np.float64)


def _cohort_has_sufficient_malicious_support(
    cohort_records: tuple[LamdaRawRecord, ...],
    rule: LabelDerivationRule,
    endpoint: CalendarMonth,
    transition_interval_months: WindowSpanMonths,
    minimum_support_per_class: int,
) -> bool:
    windows = transition_windows(endpoint, transition_interval_months)
    before_count = 0
    after_count = 0
    for record in cohort_records:
        if audited_label(rule, record).binary_label is not True:
            continue
        month = year_month_to_calendar_month(record.year_month)
        if windows.before_window_start_inclusive <= month < windows.before_window_end_exclusive:
            before_count += 1
        elif windows.after_window_start_inclusive <= month < windows.after_window_end_exclusive:
            after_count += 1
    return before_count >= minimum_support_per_class and after_count >= minimum_support_per_class


def _dominant_malicious_family_cohort(
    records: tuple[LamdaRawRecord, ...], rule: LabelDerivationRule
) -> FamilyName | None:
    counts = Counter(
        record.family
        for record in records
        if record.family is not None and audited_label(rule, record).binary_label is True
    )
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def run_lamda_identification_diagnostics(
    application: ExperimentRuntime,
) -> IdentificationDiagnosticsReport:
    raw_root = application.repository_root / "data" / "raw" / "LAMDA" / "Baseline" / "2023"
    if not raw_root.is_dir():
        LOGGER.warning("lamda identification diagnostics has no LAMDA release at %s", raw_root)
        return IdentificationDiagnosticsReport(None, 0, 0, ScientificOutcome.INSUFFICIENT_EVIDENCE)
    config = application.configuration.values
    loaded = _load_variance_filtered_lamda_dataset(
        raw_root, config.datasets.lamda.preprocessing.raw_variance_threshold_when_required
    )
    rule = label_derivation_rule(config.datasets.lamda)

    cohort = _dominant_malicious_family_cohort(loaded.records, rule)
    if cohort is None:
        LOGGER.warning("lamda identification diagnostics found no family-labeled cohort")
        return IdentificationDiagnosticsReport(None, 0, 0, ScientificOutcome.INSUFFICIENT_EVIDENCE)
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

    records_list: list[_IdentificationCutoffRecord] = []
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
            rule,
            endpoint,
            config.temporal.transition_interval_months,
            config.identification.minimum_support_per_class,
        ):
            records_list.append(
                _IdentificationCutoffRecord(
                    cutoff=endpoint,
                    cohort=cohort,
                    fitted=False,
                    abstention_reason=AbstentionReason.ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT,
                )
            )
            continue
        encoder = _train_cutoff_representation_encoder(
            application, loaded.records, loaded.features, rule, endpoint
        )
        if encoder is None:
            records_list.append(
                _IdentificationCutoffRecord(
                    cutoff=endpoint,
                    cohort=cohort,
                    fitted=False,
                    abstention_reason=AbstentionReason.ABSTAIN_INSUFFICIENT_TEMPORAL_HISTORY,
                )
            )
            continue
        embedded_features = _embed_features(encoder, loaded.features)
        embedded_cohort_features = embedded_features[cohort_mask]
        result = fit_lamda_client_constraint(
            application,
            cohort_records,
            embedded_cohort_features,
            loaded.records,
            embedded_features,
            rule,
            endpoint,
            historical_endpoints,
            earlier_malicious_endpoints,
        )
        if isinstance(result, ClientConstraintFit):
            fitted += 1
            records_list.append(
                _IdentificationCutoffRecord(
                    cutoff=endpoint,
                    cohort=cohort,
                    fitted=True,
                    selected_rank=result.selected_rank,
                    eigengap_ratio=result.eigengap_ratio,
                    beta=result.beta,
                )
            )
        else:
            records_list.append(
                _IdentificationCutoffRecord(
                    cutoff=endpoint, cohort=cohort, fitted=False, abstention_reason=result
                )
            )

    destination = (
        application.repository_root
        / config.workspace.directories.experiments
        / "prospective-evaluation"
        / "identification-diagnostics.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        _IdentificationDiagnosticsArtifact(cohort=cohort, cutoffs=records_list).model_dump_json(
            indent=_EVIDENCE_JSON_INDENT_SPACES
        ),
        encoding="utf-8",
    )
    LOGGER.info(
        "lamda identification diagnostics completed cohort=%s evaluated=%s fitted=%s",
        cohort,
        len(records_list),
        fitted,
    )
    return IdentificationDiagnosticsReport(
        cohort=cohort,
        cutoffs_evaluated=len(records_list),
        cutoffs_fitted=fitted,
        scientific_outcome=(
            ScientificOutcome.PASS if fitted > 0 else ScientificOutcome.INSUFFICIENT_EVIDENCE
        ),
    )


class _WeakEigengapStressRecord(StrictModel):
    sigma_multiplier: SensitivityMultiplier
    baseline_selected_rank: RankDimension
    perturbed_selected_rank: RankDimension
    baseline_eigengap_ratio: EigengapRatio
    perturbed_eigengap_ratio: EigengapRatio
    rank_destabilized: ValidationFlag


class _WeakEigengapStressArtifact(StrictModel):
    endpoint: CalendarMonth
    results: list[_WeakEigengapStressRecord]


@dataclass(frozen=True)
class WeakEigengapStressReport:
    endpoint: CalendarMonth | None
    results: tuple[_WeakEigengapStressRecord, ...]
    scientific_outcome: ScientificOutcome


def run_lamda_weak_eigengap_stress(application: ExperimentRuntime) -> WeakEigengapStressReport:
    raw_root = application.repository_root / "data" / "raw" / "LAMDA" / "Baseline" / "2023"
    if not raw_root.is_dir():
        LOGGER.warning("weak-eigengap stress has no LAMDA release at %s", raw_root)
        return WeakEigengapStressReport(None, (), ScientificOutcome.INSUFFICIENT_EVIDENCE)
    config = application.configuration.values
    loaded = _load_variance_filtered_lamda_dataset(
        raw_root, config.datasets.lamda.preprocessing.raw_variance_threshold_when_required
    )
    rule = label_derivation_rule(config.datasets.lamda)
    transition_interval_months = config.temporal.transition_interval_months
    history = config.temporal.historical_training_window_months

    months = np.fromiter(
        (int(year_month_to_calendar_month(record.year_month)) for record in loaded.records),
        dtype=np.int64,
        count=len(loaded.records),
    )
    month_min, month_max = int(months.min()), int(months.max())

    replicates: tuple[ControlTransitionReplicate, ...] = ()
    endpoint: CalendarMonth | None = None
    for endpoint_ordinal in range(month_max, month_min, -1):
        candidate_endpoint = calendar_month(endpoint_ordinal)
        historical_endpoints = tuple(
            calendar_month(candidate)
            for candidate in range(max(month_min, endpoint_ordinal - history), endpoint_ordinal)
        )
        candidate_replicates = control_transition_replicates(
            loaded.records, loaded.features, rule, historical_endpoints, transition_interval_months
        )
        if len(candidate_replicates) >= config.identification.minimum_control_transition_replicates:
            replicates = candidate_replicates
            endpoint = candidate_endpoint
            break
    if not replicates or endpoint is None:
        LOGGER.warning("weak-eigengap stress found no window with usable control replicates")
        return WeakEigengapStressReport(None, (), ScientificOutcome.INSUFFICIENT_EVIDENCE)

    encoder = _train_cutoff_representation_encoder(
        application, loaded.records, loaded.features, rule, endpoint
    )
    if encoder is None:
        LOGGER.warning("weak-eigengap stress could not train a cutoff-fixed encoder")
        return WeakEigengapStressReport(None, (), ScientificOutcome.INSUFFICIENT_EVIDENCE)
    embedded_features = _embed_features(encoder, loaded.features)
    historical_endpoints = tuple(
        calendar_month(candidate)
        for candidate in range(max(month_min, int(endpoint) - history), int(endpoint))
    )
    replicates = control_transition_replicates(
        loaded.records, embedded_features, rule, historical_endpoints, transition_interval_months
    )
    if len(replicates) < config.identification.minimum_control_transition_replicates:
        LOGGER.warning("weak-eigengap stress lost usable replicates after embedding")
        return WeakEigengapStressReport(None, (), ScientificOutcome.INSUFFICIENT_EVIDENCE)

    replicate_displacements = [replicate.displacement for replicate in replicates]
    replicate_supports = [
        (replicate.support_before, replicate.support_after) for replicate in replicates
    ]
    dimension = embedded_features.shape[1]
    baseline = select_stable_nuisance_rank(
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

    stacked = np.stack(replicate_displacements)
    coordinate_std = np.std(stacked, axis=0)
    finite_std = coordinate_std[np.isfinite(coordinate_std)]
    median_std = float(np.median(finite_std)) if finite_std.size else 0.0

    results: list[_WeakEigengapStressRecord] = []
    analysis_seeds = config.seeds.analysis
    for index, multiplier in enumerate(
        config.robustness.real_stress.control_transition_noise_sigma_multipliers
    ):
        rng = np.random.default_rng(analysis_seeds[index % len(analysis_seeds)])
        noise_scale = median_std * multiplier
        perturbed_displacements = [
            displacement + rng.normal(scale=noise_scale, size=dimension)
            for displacement in replicate_displacements
        ]
        perturbed = select_stable_nuisance_rank(
            replicate_displacements=perturbed_displacements,
            replicate_supports=replicate_supports,
            dimension=dimension,
            configured_maximum_rank=config.identification.nuisance_rank.maximum,
            eigengap_requirement=(
                config.identification.eigengap_ratio.default_without_nested_calibration
            ),
            rank_clip_epsilon_relative=config.numerical.rank_clip_epsilon_relative,
            scale_standardization_floor=config.numerical.scale_standardization_floor,
            bootstrap_resamples=config.identification.nuisance_rank.bootstrap_resamples,
            minimum_bootstrap_stability_fraction=(
                config.identification.nuisance_rank.minimum_bootstrap_stability_fraction
            ),
            seed=config.seeds.calibration[0],
        )
        results.append(
            _WeakEigengapStressRecord(
                sigma_multiplier=multiplier,
                baseline_selected_rank=baseline.selected_rank,
                perturbed_selected_rank=perturbed.selected_rank,
                baseline_eigengap_ratio=baseline.eigengap_ratio,
                perturbed_eigengap_ratio=perturbed.eigengap_ratio,
                rank_destabilized=(
                    perturbed.selected_rank != baseline.selected_rank or not perturbed.is_stable
                ),
            )
        )
        LOGGER.info(
            "weak-eigengap stress endpoint=%s sigma_multiplier=%s baseline_rank=%s "
            "perturbed_rank=%s destabilized=%s",
            endpoint,
            multiplier,
            baseline.selected_rank,
            perturbed.selected_rank,
            results[-1].rank_destabilized,
        )

    destination = (
        application.repository_root
        / config.workspace.directories.experiments
        / "failure-boundaries"
        / "weak-eigengap-stress.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        _WeakEigengapStressArtifact(endpoint=endpoint, results=results).model_dump_json(
            indent=_EVIDENCE_JSON_INDENT_SPACES
        ),
        encoding="utf-8",
    )
    return WeakEigengapStressReport(
        endpoint=endpoint,
        results=tuple(results),
        scientific_outcome=(
            ScientificOutcome.PASS if results else ScientificOutcome.INSUFFICIENT_EVIDENCE
        ),
    )
