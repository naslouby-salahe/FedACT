from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from pydantic import Field

from fedact.analysis.comparisons import CutoffAggregate
from fedact.analysis.metrics import EvaluationRecord, compute_evaluation_metrics
from fedact.certification.client_procedure import select_stable_nuisance_rank
from fedact.certification.dynamics import fit_scalar_model
from fedact.config.models import StrictModel
from fedact.data.ember2024 import (
    apply_log1p_transforms,
    ember2024_count_feature_mask,
    load_ember2024_records,
    validate_ember_dataset,
)
from fedact.data.lamda import (
    audited_label,
    label_derivation_rule,
    load_lamda_records,
    validate_lamda_dataset,
    year_month_to_calendar_month,
)
from fedact.data.splits import (
    CalendarMonth,
    calendar_month,
    earliest_complete_transition_endpoint,
    transition_windows,
    windowed_mean,
)
from fedact.domain.types import (
    BinaryLabel,
    CertificationStatus,
    CorrelationCoefficient,
    DatasetSelector,
    DegradationValue,
    DimensionValue,
    EvaluationCount,
    FamilyName,
    LossValue,
    MetricRate,
    ProbabilityValue,
    RankDimension,
    RelativePosixPath,
    SampleIdentifier,
    ScientificOutcome,
    SplitCutoffIdentity,
    ValidationFlag,
)
from fedact.experiments.baselines import matched_benign_subtraction, projected_point_reconstruction
from fedact.experiments.registry import ExperimentRuntime
from fedact.learning.detector import load_trained_detector, train_base_detector
from fedact.learning.hardening import (
    SampleChallengeSet,
    clean_false_negative_rate,
    harden_detector_head,
    read_challenge_sets,
)
from fedact.learning.representation import (
    DEFAULT_ENCODER_HIDDEN_DIMENSIONS,
    EMBEDDING_DIMENSION,
    RepresentationDataset,
    RepresentationEncoder,
    TrainingObservation,
    load_representation_encoder,
    train_representation_encoder,
)
from fedact.learning.scoring import score_samples

LOGGER = logging.getLogger(__name__)


class _TransferManifest(StrictModel):
    encoder_checkpoint: RelativePosixPath
    detector_checkpoint: RelativePosixPath
    feature_adapter: RelativePosixPath
    input_dimension: RankDimension = Field(gt=0)
    certificate_decisions: RelativePosixPath | None = None


class _CertificateDecisionRecord(StrictModel):
    sample_id: SampleIdentifier
    status: CertificationStatus


class _CertificateDecisionArtifact(StrictModel):
    decisions: list[_CertificateDecisionRecord]


class _CutoffComparisonRecord(StrictModel):
    cutoff_id: SplitCutoffIdentity
    certified_false_negative_rate: MetricRate | None
    ambiguous_false_negative_rate: MetricRate | None
    static_chronological_false_negative_rate: MetricRate | None = None
    hardened_false_negative_rate: MetricRate | None = None
    matched_benign_subtraction_false_negative_rate: MetricRate | None = None
    projected_point_reconstruction_false_negative_rate: MetricRate | None = None
    raw_future_transition_forecast_false_negative_rate: MetricRate | None = None


class _CutoffComparisonArtifact(StrictModel):
    comparisons: list[_CutoffComparisonRecord]


class _CentralPatternCutoffRecord(StrictModel):
    cutoff_id: SplitCutoffIdentity
    certified_precision: MetricRate | None = None
    point_selected_precision: MetricRate | None = None
    matched_random_precision: MetricRate | None = None
    matched_random_match_quality_sufficient: ValidationFlag = False


class _CentralPatternArtifact(StrictModel):
    cutoffs: list[_CentralPatternCutoffRecord]
    rank_alignment_spearman_rho: CorrelationCoefficient | None = None


def read_central_pattern_cutoff_aggregates(
    application: ExperimentRuntime,
) -> tuple[tuple[CutoffAggregate, ...], tuple[CutoffAggregate, ...]]:
    source = (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / "action-certificate-validation"
        / "central-pattern.json"
    )
    if not source.is_file():
        return (), ()
    artifact = _CentralPatternArtifact.model_validate_json(source.read_text(encoding="utf-8"))
    certified = tuple(
        CutoffAggregate(cutoff.cutoff_id, cutoff.certified_precision, None)
        for cutoff in artifact.cutoffs
        if cutoff.matched_random_match_quality_sufficient
    )
    matched_random = tuple(
        CutoffAggregate(cutoff.cutoff_id, cutoff.matched_random_precision, None)
        for cutoff in artifact.cutoffs
        if cutoff.matched_random_match_quality_sufficient
    )
    return certified, matched_random


@dataclass(frozen=True)
class _FeatureAdapter:
    mean: np.ndarray
    scale: np.ndarray
    projection: np.ndarray


def _workspace_path(application: ExperimentRuntime, relative_path: RelativePosixPath) -> Path:
    resolved = (application.repository_root / relative_path).resolve()
    if not resolved.is_relative_to(application.repository_root.resolve()):
        raise ValueError(f"transfer artifact escapes repository root: {relative_path}")
    return resolved


def _load_feature_adapter(source: Path, input_dimension: DimensionValue) -> _FeatureAdapter:
    if not source.is_file():
        raise FileNotFoundError(f"locked feature adapter is missing: {source}")
    with np.load(source) as payload:
        mean = payload["mean"]
        scale = payload["scale"]
        projection = payload["projection"]
    if mean.ndim != 1 or scale.shape != mean.shape or projection.shape[0] != mean.size:
        raise ValueError("feature adapter arrays have incompatible dimensions")
    if projection.shape[1] != input_dimension:
        raise ValueError("feature adapter output does not match locked encoder dimension")
    if not np.isfinite(mean).all() or not np.isfinite(scale).all() or np.any(scale <= 0.0):
        raise ValueError("feature adapter has invalid fitted normalization parameters")
    return _FeatureAdapter(
        mean=np.asarray(mean, dtype=np.float32),
        scale=np.asarray(scale, dtype=np.float32),
        projection=np.asarray(projection, dtype=np.float32),
    )


def _labeled_target_value(value: BinaryLabel | None) -> BinaryLabel:
    if value is None:
        raise ValueError("selected EMBER evaluation row has no label")
    return value


def _binary_cross_entropy(label: BinaryLabel, probability: MetricRate) -> LossValue:
    bounded = np.clip(probability, np.finfo(np.float64).eps, 1.0 - np.finfo(np.float64).eps)
    return float(-np.log(bounded if label else 1.0 - bounded))


def _group_false_negative_rate(records: tuple[EvaluationRecord, ...]) -> MetricRate | None:
    malicious = tuple(record for record in records if record.true_label)
    if not malicious:
        return None
    return sum(record.predicted_score < 0.5 for record in malicious) / len(malicious)


def read_prospective_cutoff_aggregates(
    application: ExperimentRuntime,
) -> tuple[
    tuple[CutoffAggregate, ...],
    tuple[CutoffAggregate, ...],
    tuple[CutoffAggregate, ...],
    tuple[CutoffAggregate, ...],
]:
    source = (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / "prospective-evaluation"
        / "cutoff-comparisons.json"
    )
    if not source.is_file():
        return (), (), (), ()
    artifact = _CutoffComparisonArtifact.model_validate_json(source.read_text(encoding="utf-8"))
    certified = tuple(
        CutoffAggregate(comparison.cutoff_id, comparison.certified_false_negative_rate, None)
        for comparison in artifact.comparisons
    )
    ambiguous = tuple(
        CutoffAggregate(comparison.cutoff_id, comparison.ambiguous_false_negative_rate, None)
        for comparison in artifact.comparisons
    )
    hardened = tuple(
        CutoffAggregate(comparison.cutoff_id, comparison.hardened_false_negative_rate, None)
        for comparison in artifact.comparisons
    )
    static_chronological = tuple(
        CutoffAggregate(
            comparison.cutoff_id, comparison.static_chronological_false_negative_rate, None
        )
        for comparison in artifact.comparisons
    )
    return certified, ambiguous, hardened, static_chronological


@dataclass(frozen=True)
class CrossCorpusReport:
    target_corpora_tested: EvaluationCount
    mean_transfer_fnr: MetricRate
    certified_false_negative_rate: MetricRate | None
    ambiguous_false_negative_rate: MetricRate | None
    transfer_supported: ValidationFlag
    scientific_outcome: ScientificOutcome
    true_positive_rate: MetricRate | None = None
    false_positive_rate: MetricRate | None = None
    abstention_rate: MetricRate | None = None
    pr_auc: MetricRate | None = None
    roc_auc: MetricRate | None = None

    @property
    def generalization_valid(self) -> ValidationFlag:
        return self.transfer_supported


@dataclass(frozen=True)
class ProspectiveEvaluationReport:
    total_evaluations: EvaluationCount
    mean_false_negative_rate: MetricRate
    mean_certification_rate: MetricRate
    static_chronological_false_negative_rate: MetricRate
    early_horizon_fnr_reduction_percentage_points: DegradationValue
    clean_fnr_degradation_percentage_points: DegradationValue
    scientific_outcome: ScientificOutcome
    matched_benign_subtraction_false_negative_rate: MetricRate | None = None
    projected_point_reconstruction_false_negative_rate: MetricRate | None = None
    raw_future_transition_forecast_false_negative_rate: MetricRate | None = None
    mean_true_positive_rate: MetricRate | None = None
    mean_false_positive_rate: MetricRate | None = None
    mean_abstention_rate: MetricRate | None = None
    pr_auc: MetricRate | None = None
    roc_auc: MetricRate | None = None


@dataclass(frozen=True)
class _LamdaPopulation:
    features: np.ndarray
    labels: np.ndarray
    months: np.ndarray
    sample_ids: tuple[SampleIdentifier, ...]
    family: tuple[FamilyName | None, ...]


def _load_lamda_population(application: ExperimentRuntime) -> _LamdaPopulation | None:
    raw_root = application.repository_root / "data" / "raw" / "LAMDA" / "Baseline" / "2023"
    if not raw_root.is_dir():
        LOGGER.warning("prospective evaluation has no LAMDA release at %s", raw_root)
        return None
    loaded = load_lamda_records(raw_root)
    validate_lamda_dataset(loaded)
    rule = label_derivation_rule(application.configuration.values.datasets.lamda)
    keep = np.fromiter(
        (audited_label(rule, record).binary_label is not None for record in loaded.records),
        dtype=bool,
        count=len(loaded.records),
    )
    if not np.any(keep):
        LOGGER.warning("LAMDA contains no rows with an auditable binary label")
        return None
    records = tuple(
        record for record, retained in zip(loaded.records, keep, strict=True) if retained
    )
    labels = np.fromiter(
        (bool(audited_label(rule, record).binary_label) for record in records),
        dtype=bool,
        count=len(records),
    )
    months = np.fromiter(
        (int(year_month_to_calendar_month(record.year_month)) for record in records),
        dtype=np.int64,
        count=len(records),
    )
    return _LamdaPopulation(
        features=np.ascontiguousarray(loaded.features[keep], dtype=np.float64),
        labels=labels,
        months=months,
        sample_ids=tuple(record.sample_hash for record in records),
        family=tuple(record.family for record in records),
    )


def _eligible_cutoffs(
    application: ExperimentRuntime, population: _LamdaPopulation
) -> tuple[int, ...]:
    config = application.configuration.values
    horizon = config.temporal.primary_confirmatory_horizon_months
    history = config.temporal.historical_training_window_months
    minimum = config.identification.minimum_support_per_class
    eligible: list[int] = []
    for cutoff in range(int(population.months.min()), int(population.months.max()) - horizon + 1):
        historical = (population.months >= cutoff - history) & (population.months < cutoff)
        later = (population.months >= cutoff) & (population.months < cutoff + horizon)
        if not historical.any() or not later.any():
            continue
        historical_labels = population.labels[historical]
        later_labels = population.labels[later]
        if (
            np.count_nonzero(historical_labels) >= minimum
            and np.count_nonzero(~historical_labels) >= minimum
            and np.count_nonzero(later_labels) > 0
            and np.count_nonzero(~later_labels) > 0
        ):
            eligible.append(cutoff)
    return tuple(eligible)


def run_cross_corpus_generalization(application: ExperimentRuntime) -> CrossCorpusReport:
    manifest_path = (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / "cross-corpus"
        / "transfer.json"
    )
    target_root = application.repository_root / "data" / "raw" / "EMBER2024"
    if not manifest_path.is_file() or not target_root.is_dir():
        LOGGER.warning(
            "cross-corpus transfer requires a locked transfer manifest=%s target=%s",
            manifest_path.is_file(),
            target_root.is_dir(),
        )
        return CrossCorpusReport(0, 0.0, None, None, False, ScientificOutcome.INSUFFICIENT_EVIDENCE)
    manifest = _TransferManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    encoder_path = _workspace_path(application, manifest.encoder_checkpoint)
    detector_path = _workspace_path(application, manifest.detector_checkpoint)
    adapter = _load_feature_adapter(
        _workspace_path(application, manifest.feature_adapter), manifest.input_dimension
    )
    if not encoder_path.is_file() or not detector_path.is_file():
        raise FileNotFoundError("locked source encoder or detector checkpoint is missing")
    target = load_ember2024_records(target_root)
    validate_ember_dataset(target)
    labeled = np.fromiter(
        (record.label is not None for record in target.records),
        dtype=bool,
        count=len(target.records),
    )
    if not labeled.any():
        return CrossCorpusReport(0, 0.0, None, None, False, ScientificOutcome.INSUFFICIENT_EVIDENCE)
    target_features = apply_log1p_transforms(
        target.features[labeled], ember2024_count_feature_mask()
    )
    if target_features.shape[1] != adapter.mean.size:
        raise ValueError("locked adapter input does not match EMBER feature schema")
    adapted = ((target_features - adapter.mean) / adapter.scale) @ adapter.projection
    encoder = load_representation_encoder(
        encoder_path,
        manifest.input_dimension,
        DEFAULT_ENCODER_HIDDEN_DIMENSIONS,
        EMBEDDING_DIMENSION,
    )
    detector = load_trained_detector(detector_path, EMBEDDING_DIMENSION)
    selected_records = tuple(
        record for record, include in zip(target.records, labeled, strict=True) if include
    )
    scores = score_samples(
        encoder,
        detector,
        tuple(record.sample_hash for record in selected_records),
        torch.tensor(adapted, dtype=torch.float32),
    )
    if manifest.certificate_decisions is None:
        LOGGER.warning(
            "cross-corpus transfer manifest has no locked certificate decisions; a "
            "detector-performance win alone is insufficient for a generalization claim"
        )
        certified_samples: frozenset[SampleIdentifier] = frozenset()
    else:
        decisions_path = _workspace_path(application, manifest.certificate_decisions)
        decision_artifact = _CertificateDecisionArtifact.model_validate_json(
            decisions_path.read_text(encoding="utf-8")
        )
        certified_samples = frozenset(
            decision.sample_id
            for decision in decision_artifact.decisions
            if decision.status is CertificationStatus.CERTIFIED_POSITIVE
        )
    evaluations = tuple(
        EvaluationRecord(
            dataset=DatasetSelector.EMBER2024,
            cutoff_id=SplitCutoffIdentity("ember2024-locked-transfer"),
            sample_id=record.sample_hash,
            horizon_step=1,
            true_label=_labeled_target_value(record.label),
            predicted_score=score.probability,
            is_certified=record.sample_hash in certified_samples,
            clean_loss=0.0,
        )
        for record, score in zip(selected_records, scores, strict=True)
    )
    metrics = compute_evaluation_metrics(evaluations)
    certified_records = tuple(record for record in evaluations if record.is_certified)
    ambiguous_records = tuple(
        record
        for record in evaluations
        if not record.is_certified and record.sample_id not in certified_samples
    )
    certified_fnr = _group_false_negative_rate(certified_records)
    ambiguous_fnr = _group_false_negative_rate(ambiguous_records)
    transfer_supported = (
        certified_samples != frozenset()
        and certified_fnr is not None
        and ambiguous_fnr is not None
        and certified_fnr <= ambiguous_fnr
    )
    LOGGER.info(
        "cross-corpus locked transfer scored target_rows=%s certified=%s transfer_supported=%s",
        len(evaluations),
        len(certified_records),
        transfer_supported,
    )
    return CrossCorpusReport(
        len(evaluations),
        metrics.false_negative_rate,
        certified_fnr,
        ambiguous_fnr,
        transfer_supported,
        ScientificOutcome.PASS if transfer_supported else ScientificOutcome.INSUFFICIENT_EVIDENCE,
        true_positive_rate=metrics.true_positive_rate,
        false_positive_rate=metrics.false_positive_rate,
        abstention_rate=metrics.abstention_rate,
        pr_auc=metrics.pr_auc,
        roc_auc=metrics.roc_auc,
    )


@dataclass(frozen=True)
class _CutoffScoring:
    sample_ids: tuple[SampleIdentifier, ...]
    scores: tuple[ProbabilityValue, ...]
    static_chronological_scores: tuple[ProbabilityValue, ...]
    clean_fnr_degradation_percentage_points: DegradationValue
    matched_benign_subtraction_scores: tuple[ProbabilityValue, ...] | None = None
    projected_point_reconstruction_scores: tuple[ProbabilityValue, ...] | None = None
    raw_future_transition_forecast_scores: tuple[ProbabilityValue, ...] | None = None


def _dominant_malicious_family(
    training: tuple[TrainingObservation, ...],
    family_by_sample: dict[SampleIdentifier, FamilyName | None],
) -> FamilyName | None:
    counts = Counter(
        family_by_sample[obs.sample_id]
        for obs in training
        if obs.label and family_by_sample[obs.sample_id]
    )
    if not counts:
        return None
    return counts.most_common(1)[0][0]


def _embedded_transition_displacement(
    embedded_features: np.ndarray,
    months: np.ndarray,
    class_mask: np.ndarray,
    endpoint: CalendarMonth,
    transition_interval_months: int,
) -> np.ndarray | None:
    windows = transition_windows(endpoint, transition_interval_months)
    class_features = embedded_features[class_mask]
    class_months = months[class_mask]
    before_mean, before_support = windowed_mean(
        class_features,
        class_months,
        windows.before_window_start_inclusive,
        windows.before_window_end_exclusive,
    )
    after_mean, after_support = windowed_mean(
        class_features,
        class_months,
        windows.after_window_start_inclusive,
        windows.after_window_end_exclusive,
    )
    if before_support == 0 or after_support == 0:
        return None
    return after_mean - before_mean


def _matched_benign_subtraction_challenges(
    training: tuple[TrainingObservation, ...],
    encoder: RepresentationEncoder,
    family_by_sample: dict[SampleIdentifier, FamilyName | None],
    endpoint: CalendarMonth,
    transition_interval_months: int,
) -> tuple[SampleChallengeSet, ...]:
    cohort = _dominant_malicious_family(training, family_by_sample)
    if cohort is None:
        return ()
    with torch.no_grad():
        embedded = (
            encoder(
                torch.stack(
                    [
                        torch.tensor(obs.features, dtype=torch.float32)
                        if isinstance(obs.features, tuple)
                        else obs.features
                        for obs in training
                    ]
                )
            )
            .numpy()
            .astype(np.float64)
        )
    training_months = np.fromiter(
        (obs.month_index for obs in training), dtype=np.int64, count=len(training)
    )
    training_labels = np.fromiter((obs.label for obs in training), dtype=bool, count=len(training))
    cohort_malicious_mask = np.fromiter(
        (obs.label and family_by_sample[obs.sample_id] == cohort for obs in training),
        dtype=bool,
        count=len(training),
    )
    control_mask = ~training_labels
    malicious_displacement = _embedded_transition_displacement(
        embedded, training_months, cohort_malicious_mask, endpoint, transition_interval_months
    )
    control_displacement = _embedded_transition_displacement(
        embedded, training_months, control_mask, endpoint, transition_interval_months
    )
    if malicious_displacement is None or control_displacement is None:
        return ()
    estimate = matched_benign_subtraction(malicious_displacement, control_displacement)
    return tuple(
        SampleChallengeSet(
            source_sample_id=obs.sample_id,
            challenge_embeddings=(
                tuple(float(value) for value in embedded[index] + estimate.estimated_displacement),
            ),
        )
        for index, obs in enumerate(training)
        if cohort_malicious_mask[index]
    )


def _embedded_control_replicates(
    embedded_features: np.ndarray,
    months: np.ndarray,
    control_mask: np.ndarray,
    candidate_endpoints: Sequence[CalendarMonth],
    transition_interval_months: int,
) -> list[tuple[np.ndarray, int, int]]:
    windows_by_endpoint = [
        transition_windows(e, transition_interval_months) for e in candidate_endpoints
    ]
    control_features = embedded_features[control_mask]
    control_months = months[control_mask]
    replicates: list[tuple[np.ndarray, int, int]] = []
    for windows in windows_by_endpoint:
        before_mean, before_support = windowed_mean(
            control_features,
            control_months,
            windows.before_window_start_inclusive,
            windows.before_window_end_exclusive,
        )
        after_mean, after_support = windowed_mean(
            control_features,
            control_months,
            windows.after_window_start_inclusive,
            windows.after_window_end_exclusive,
        )
        if before_support == 0 or after_support == 0:
            continue
        replicates.append((after_mean - before_mean, before_support, after_support))
    return replicates


def _projected_point_reconstruction_challenges(
    application: ExperimentRuntime,
    training: tuple[TrainingObservation, ...],
    encoder: RepresentationEncoder,
    family_by_sample: dict[SampleIdentifier, FamilyName | None],
    endpoint: CalendarMonth,
    historical_endpoints: tuple[CalendarMonth, ...],
    transition_interval_months: int,
) -> tuple[SampleChallengeSet, ...]:
    config = application.configuration.values
    cohort = _dominant_malicious_family(training, family_by_sample)
    if cohort is None:
        return ()
    with torch.no_grad():
        embedded = (
            encoder(
                torch.stack(
                    [
                        torch.tensor(obs.features, dtype=torch.float32)
                        if isinstance(obs.features, tuple)
                        else obs.features
                        for obs in training
                    ]
                )
            )
            .numpy()
            .astype(np.float64)
        )
    training_months = np.fromiter(
        (obs.month_index for obs in training), dtype=np.int64, count=len(training)
    )
    training_labels = np.fromiter((obs.label for obs in training), dtype=bool, count=len(training))
    cohort_malicious_mask = np.fromiter(
        (obs.label and family_by_sample[obs.sample_id] == cohort for obs in training),
        dtype=bool,
        count=len(training),
    )
    control_mask = ~training_labels
    malicious_displacement = _embedded_transition_displacement(
        embedded, training_months, cohort_malicious_mask, endpoint, transition_interval_months
    )
    if malicious_displacement is None:
        return ()
    replicates = _embedded_control_replicates(
        embedded, training_months, control_mask, historical_endpoints, transition_interval_months
    )
    if len(replicates) < config.identification.minimum_control_transition_replicates:
        return ()
    replicate_displacements = [displacement for displacement, _before, _after in replicates]
    replicate_supports = [(before, after) for _displacement, before, after in replicates]
    dimension = embedded.shape[1]
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
    if rank_selection.eigengap_ratio < 1.0 or not rank_selection.is_stable:
        return ()
    estimate = projected_point_reconstruction(malicious_displacement, rank_selection.subspace)
    return tuple(
        SampleChallengeSet(
            source_sample_id=obs.sample_id,
            challenge_embeddings=(
                tuple(float(value) for value in embedded[index] + estimate.estimated_displacement),
            ),
        )
        for index, obs in enumerate(training)
        if cohort_malicious_mask[index]
    )


def _raw_future_transition_forecast_challenges(
    application: ExperimentRuntime,
    training: tuple[TrainingObservation, ...],
    encoder: RepresentationEncoder,
    family_by_sample: dict[SampleIdentifier, FamilyName | None],
    endpoint: CalendarMonth,
    historical_endpoints: tuple[CalendarMonth, ...],
    transition_interval_months: int,
) -> tuple[SampleChallengeSet, ...]:
    config = application.configuration.values
    cohort = _dominant_malicious_family(training, family_by_sample)
    if cohort is None:
        return ()
    with torch.no_grad():
        embedded = (
            encoder(
                torch.stack(
                    [
                        torch.tensor(obs.features, dtype=torch.float32)
                        if isinstance(obs.features, tuple)
                        else obs.features
                        for obs in training
                    ]
                )
            )
            .numpy()
            .astype(np.float64)
        )
    training_months = np.fromiter(
        (obs.month_index for obs in training), dtype=np.int64, count=len(training)
    )
    cohort_malicious_mask = np.fromiter(
        (obs.label and family_by_sample[obs.sample_id] == cohort for obs in training),
        dtype=bool,
        count=len(training),
    )
    centers: list[np.ndarray] = []
    for candidate_endpoint in (*historical_endpoints, endpoint):
        displacement = _embedded_transition_displacement(
            embedded,
            training_months,
            cohort_malicious_mask,
            candidate_endpoint,
            transition_interval_months,
        )
        if displacement is not None:
            centers.append(displacement)
    minimum_pairs = config.temporal.temporal_model.minimum_consecutive_pairs
    if len(centers) < minimum_pairs + 1:
        return ()
    fit = fit_scalar_model(centers, config.temporal.temporal_model.maximum_scalar_coefficient)
    forecast = fit.coefficient * centers[-1]
    return tuple(
        SampleChallengeSet(
            source_sample_id=obs.sample_id,
            challenge_embeddings=(tuple(float(value) for value in embedded[index] + forecast),),
        )
        for index, obs in enumerate(training)
        if cohort_malicious_mask[index]
    )


def _score_cutoff_population(
    application: ExperimentRuntime,
    population: _LamdaPopulation,
    historical: np.ndarray,
    later: np.ndarray,
) -> _CutoffScoring | None:
    config = application.configuration.values
    observations = tuple(
        TrainingObservation(
            sample_id=sample_id,
            features=torch.tensor(feature, dtype=torch.float32),
            month_index=int(month),
            label=bool(label),
        )
        for sample_id, feature, month, label in zip(
            np.asarray(population.sample_ids, dtype=object)[historical],
            population.features[historical],
            population.months[historical],
            population.labels[historical],
            strict=True,
        )
    )
    validation_month = max(item.month_index for item in observations)
    training = tuple(item for item in observations if item.month_index < validation_month)
    validation = tuple(item for item in observations if item.month_index == validation_month)
    if not training or not validation:
        return None
    encoder, encoder_selection = train_representation_encoder(
        RepresentationDataset(training),
        RepresentationDataset(validation),
        population.features.shape[1],
        DEFAULT_ENCODER_HIDDEN_DIMENSIONS,
        EMBEDDING_DIMENSION,
        config.training.maximum_epochs,
        config.training.batch_size,
        config.training.initial_learning_rate,
        0.0,
        config.seeds.representation[0],
        config.numerical.projection_tie_tolerance,
    )
    LOGGER.info("selected representation checkpoint epoch=%s", encoder_selection.selected_epoch)
    detector = train_base_detector(
        encoder,
        RepresentationDataset(training).feature_tensor(),
        RepresentationDataset(training).label_tensor(),
        RepresentationDataset(validation).feature_tensor(),
        RepresentationDataset(validation).label_tensor(),
        config.training.maximum_epochs,
        config.training.batch_size,
        config.training.initial_learning_rate,
        0.0,
        config.seeds.representation[0],
        config.seeds.detector_training[0],
        config.numerical.projection_tie_tolerance,
    ).detector
    pristine_detector = detector
    sample_ids = tuple(np.asarray(population.sample_ids, dtype=object)[later])
    later_features = torch.tensor(population.features[later], dtype=torch.float32)
    static_chronological_scored = score_samples(encoder, detector, sample_ids, later_features)

    challenge_file = (
        application.repository_root
        / config.workspace.directories.experiments
        / "action-certificate-validation"
        / "challenges.json"
    )
    clean_fnr_degradation: DegradationValue = 0.0
    if challenge_file.is_file():
        challenges = read_challenge_sets(challenge_file)
        if challenges:
            hardening = harden_detector_head(
                encoder,
                detector,
                training,
                validation,
                challenges,
                clean_false_negative_rate(detector, encoder, validation),
                config.training.initial_learning_rate,
                config.training.final_learning_rate,
                config.training.maximum_epochs,
                config.hardening.weight.maximum_clean_fnr_degradation_percentage_points,
                config.numerical.projection_tie_tolerance,
                config.hardening.weight.candidates[0],
            )
            detector = hardening.detector
            clean_fnr_degradation = hardening.clean_fnr_degradation_percentage_points
    scored = score_samples(encoder, detector, sample_ids, later_features)

    matched_benign_subtraction_scores: tuple[ProbabilityValue, ...] | None = None
    projected_point_reconstruction_scores: tuple[ProbabilityValue, ...] | None = None
    raw_future_transition_forecast_scores: tuple[ProbabilityValue, ...] | None = None
    endpoint = calendar_month(validation_month + 1)
    earliest_valid_transition_endpoint = earliest_complete_transition_endpoint(
        calendar_month(0), config.temporal.transition_interval_months
    )
    family_by_sample = dict(zip(population.sample_ids, population.family, strict=True))
    matched_challenges: tuple[SampleChallengeSet, ...] = ()
    if endpoint >= earliest_valid_transition_endpoint:
        matched_challenges = _matched_benign_subtraction_challenges(
            training,
            encoder,
            family_by_sample,
            endpoint,
            config.temporal.transition_interval_months,
        )
    if matched_challenges:
        matched_hardening = harden_detector_head(
            encoder,
            pristine_detector,
            training,
            validation,
            matched_challenges,
            clean_false_negative_rate(pristine_detector, encoder, validation),
            config.training.initial_learning_rate,
            config.training.final_learning_rate,
            config.training.maximum_epochs,
            config.hardening.weight.maximum_clean_fnr_degradation_percentage_points,
            config.numerical.projection_tie_tolerance,
            config.hardening.weight.candidates[0],
        )
        matched_scored = score_samples(
            encoder, matched_hardening.detector, sample_ids, later_features
        )
        matched_benign_subtraction_scores = tuple(score.probability for score in matched_scored)

    training_month_min = min(obs.month_index for obs in training)
    earliest_endpoint = earliest_complete_transition_endpoint(
        calendar_month(training_month_min), config.temporal.transition_interval_months
    )
    historical_endpoints = tuple(
        calendar_month(candidate) for candidate in range(int(earliest_endpoint), int(endpoint))
    )
    projected_challenges: tuple[SampleChallengeSet, ...] = ()
    if endpoint >= earliest_valid_transition_endpoint:
        projected_challenges = _projected_point_reconstruction_challenges(
            application,
            training,
            encoder,
            family_by_sample,
            endpoint,
            historical_endpoints,
            config.temporal.transition_interval_months,
        )
    if projected_challenges:
        projected_hardening = harden_detector_head(
            encoder,
            pristine_detector,
            training,
            validation,
            projected_challenges,
            clean_false_negative_rate(pristine_detector, encoder, validation),
            config.training.initial_learning_rate,
            config.training.final_learning_rate,
            config.training.maximum_epochs,
            config.hardening.weight.maximum_clean_fnr_degradation_percentage_points,
            config.numerical.projection_tie_tolerance,
            config.hardening.weight.candidates[0],
        )
        projected_scored = score_samples(
            encoder, projected_hardening.detector, sample_ids, later_features
        )
        projected_point_reconstruction_scores = tuple(
            score.probability for score in projected_scored
        )

    forecast_challenges: tuple[SampleChallengeSet, ...] = ()
    if endpoint >= earliest_valid_transition_endpoint:
        forecast_challenges = _raw_future_transition_forecast_challenges(
            application,
            training,
            encoder,
            family_by_sample,
            endpoint,
            historical_endpoints,
            config.temporal.transition_interval_months,
        )
    if forecast_challenges:
        forecast_hardening = harden_detector_head(
            encoder,
            pristine_detector,
            training,
            validation,
            forecast_challenges,
            clean_false_negative_rate(pristine_detector, encoder, validation),
            config.training.initial_learning_rate,
            config.training.final_learning_rate,
            config.training.maximum_epochs,
            config.hardening.weight.maximum_clean_fnr_degradation_percentage_points,
            config.numerical.projection_tie_tolerance,
            config.hardening.weight.candidates[0],
        )
        forecast_scored = score_samples(
            encoder, forecast_hardening.detector, sample_ids, later_features
        )
        raw_future_transition_forecast_scores = tuple(
            score.probability for score in forecast_scored
        )

    return _CutoffScoring(
        sample_ids=sample_ids,
        scores=tuple(score.probability for score in scored),
        static_chronological_scores=tuple(
            score.probability for score in static_chronological_scored
        ),
        clean_fnr_degradation_percentage_points=clean_fnr_degradation,
        matched_benign_subtraction_scores=matched_benign_subtraction_scores,
        projected_point_reconstruction_scores=projected_point_reconstruction_scores,
        raw_future_transition_forecast_scores=raw_future_transition_forecast_scores,
    )


def run_prospective_fedact_evaluation(
    application: ExperimentRuntime,
) -> ProspectiveEvaluationReport:
    certificate_decisions = (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / "action-certificate-validation"
        / "certificate-decisions.json"
    )
    if not certificate_decisions.is_file():
        LOGGER.warning("prospective evaluation requires completed action-certificate evidence")
        return ProspectiveEvaluationReport(
            0, 0.0, 0.0, 0.0, 0.0, 0.0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    decision_artifact = _CertificateDecisionArtifact.model_validate_json(
        certificate_decisions.read_text(encoding="utf-8")
    )
    certified_samples = frozenset(
        decision.sample_id
        for decision in decision_artifact.decisions
        if decision.status is CertificationStatus.CERTIFIED_POSITIVE
    )
    population = _load_lamda_population(application)
    if population is None:
        return ProspectiveEvaluationReport(
            0, 0.0, 0.0, 0.0, 0.0, 0.0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    cutoffs = _eligible_cutoffs(application, population)
    if not cutoffs:
        LOGGER.warning("no LAMDA cutoff satisfies configured history/support/horizon requirements")
        return ProspectiveEvaluationReport(
            0, 0.0, 0.0, 0.0, 0.0, 0.0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )

    config = application.configuration.values
    records: list[EvaluationRecord] = []
    comparisons: list[_CutoffComparisonRecord] = []
    clean_fnr_degradations: list[DegradationValue] = []
    static_chronological_records: list[EvaluationRecord] = []
    for cutoff in cutoffs:
        historical = (
            population.months >= cutoff - config.temporal.historical_training_window_months
        ) & (population.months < cutoff)
        later = (population.months >= cutoff) & (
            population.months < cutoff + config.temporal.primary_confirmatory_horizon_months
        )
        scored_population = _score_cutoff_population(application, population, historical, later)
        if scored_population is None:
            LOGGER.warning("cutoff has no disjoint chronological validation month: %s", cutoff)
            continue
        cutoff_id = SplitCutoffIdentity(f"lamda-{cutoff}")
        cutoff_records = tuple(
            EvaluationRecord(
                dataset=DatasetSelector.LAMDA,
                cutoff_id=cutoff_id,
                sample_id=sample_id,
                horizon_step=1,
                true_label=label,
                predicted_score=score,
                is_certified=sample_id in certified_samples,
                clean_loss=_binary_cross_entropy(label, score),
            )
            for sample_id, label, score in zip(
                scored_population.sample_ids,
                population.labels[later],
                scored_population.scores,
                strict=True,
            )
        )
        records.extend(cutoff_records)
        clean_fnr_degradations.append(scored_population.clean_fnr_degradation_percentage_points)
        certified_records = tuple(record for record in cutoff_records if record.is_certified)
        point_ambiguous_records = tuple(
            record
            for record in cutoff_records
            if not record.is_certified and record.sample_id not in certified_samples
        )
        cutoff_static_records = tuple(
            EvaluationRecord(
                dataset=DatasetSelector.LAMDA,
                cutoff_id=cutoff_id,
                sample_id=sample_id,
                horizon_step=1,
                true_label=label,
                predicted_score=score,
                is_certified=False,
                clean_loss=_binary_cross_entropy(label, score),
            )
            for sample_id, label, score in zip(
                scored_population.sample_ids,
                population.labels[later],
                scored_population.static_chronological_scores,
                strict=True,
            )
        )
        static_chronological_records.extend(cutoff_static_records)
        matched_benign_subtraction_fnr: MetricRate | None = None
        if scored_population.matched_benign_subtraction_scores is not None:
            matched_records = tuple(
                EvaluationRecord(
                    dataset=DatasetSelector.LAMDA,
                    cutoff_id=cutoff_id,
                    sample_id=sample_id,
                    horizon_step=1,
                    true_label=label,
                    predicted_score=score,
                    is_certified=False,
                    clean_loss=_binary_cross_entropy(label, score),
                )
                for sample_id, label, score in zip(
                    scored_population.sample_ids,
                    population.labels[later],
                    scored_population.matched_benign_subtraction_scores,
                    strict=True,
                )
            )
            matched_benign_subtraction_fnr = _group_false_negative_rate(matched_records)
        projected_point_reconstruction_fnr: MetricRate | None = None
        if scored_population.projected_point_reconstruction_scores is not None:
            projected_records = tuple(
                EvaluationRecord(
                    dataset=DatasetSelector.LAMDA,
                    cutoff_id=cutoff_id,
                    sample_id=sample_id,
                    horizon_step=1,
                    true_label=label,
                    predicted_score=score,
                    is_certified=False,
                    clean_loss=_binary_cross_entropy(label, score),
                )
                for sample_id, label, score in zip(
                    scored_population.sample_ids,
                    population.labels[later],
                    scored_population.projected_point_reconstruction_scores,
                    strict=True,
                )
            )
            projected_point_reconstruction_fnr = _group_false_negative_rate(projected_records)
        raw_future_transition_forecast_fnr: MetricRate | None = None
        if scored_population.raw_future_transition_forecast_scores is not None:
            forecast_records = tuple(
                EvaluationRecord(
                    dataset=DatasetSelector.LAMDA,
                    cutoff_id=cutoff_id,
                    sample_id=sample_id,
                    horizon_step=1,
                    true_label=label,
                    predicted_score=score,
                    is_certified=False,
                    clean_loss=_binary_cross_entropy(label, score),
                )
                for sample_id, label, score in zip(
                    scored_population.sample_ids,
                    population.labels[later],
                    scored_population.raw_future_transition_forecast_scores,
                    strict=True,
                )
            )
            raw_future_transition_forecast_fnr = _group_false_negative_rate(forecast_records)
        comparisons.append(
            _CutoffComparisonRecord(
                cutoff_id=cutoff_id,
                certified_false_negative_rate=_group_false_negative_rate(certified_records),
                ambiguous_false_negative_rate=_group_false_negative_rate(point_ambiguous_records),
                static_chronological_false_negative_rate=_group_false_negative_rate(
                    cutoff_static_records
                ),
                hardened_false_negative_rate=_group_false_negative_rate(cutoff_records),
                matched_benign_subtraction_false_negative_rate=matched_benign_subtraction_fnr,
                projected_point_reconstruction_false_negative_rate=projected_point_reconstruction_fnr,
                raw_future_transition_forecast_false_negative_rate=raw_future_transition_forecast_fnr,
            )
        )
        LOGGER.info("prospective evaluated cutoff=%s rows=%s", cutoff_id, len(cutoff_records))
    if not records:
        return ProspectiveEvaluationReport(
            0, 0.0, 0.0, 0.0, 0.0, 0.0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    metrics = compute_evaluation_metrics(tuple(records))
    static_chronological_metrics = compute_evaluation_metrics(tuple(static_chronological_records))
    early_horizon_fnr_reduction = (
        static_chronological_metrics.false_negative_rate - metrics.false_negative_rate
    ) * 100.0
    comparison = _CutoffComparisonArtifact(comparisons=comparisons)
    comparison_destination = (
        application.repository_root
        / config.workspace.directories.experiments
        / "prospective-evaluation"
        / "cutoff-comparisons.json"
    )
    comparison_destination.parent.mkdir(parents=True, exist_ok=True)
    comparison_destination.write_text(comparison.model_dump_json(indent=2), encoding="utf-8")
    mean_clean_fnr_degradation = (
        sum(clean_fnr_degradations) / len(clean_fnr_degradations) if clean_fnr_degradations else 0.0
    )
    certified_fnrs = [
        comparison_record.certified_false_negative_rate
        for comparison_record in comparisons
        if comparison_record.certified_false_negative_rate is not None
    ]
    ambiguous_fnrs = [
        comparison_record.ambiguous_false_negative_rate
        for comparison_record in comparisons
        if comparison_record.ambiguous_false_negative_rate is not None
    ]
    certification_mechanism_supported = (
        bool(certified_fnrs)
        and bool(ambiguous_fnrs)
        and (sum(certified_fnrs) / len(certified_fnrs))
        <= (sum(ambiguous_fnrs) / len(ambiguous_fnrs))
    )
    matched_benign_subtraction_fnrs = [
        comparison_record.matched_benign_subtraction_false_negative_rate
        for comparison_record in comparisons
        if comparison_record.matched_benign_subtraction_false_negative_rate is not None
    ]
    mean_matched_benign_subtraction_fnr = (
        sum(matched_benign_subtraction_fnrs) / len(matched_benign_subtraction_fnrs)
        if matched_benign_subtraction_fnrs
        else None
    )
    projected_point_reconstruction_fnrs = [
        comparison_record.projected_point_reconstruction_false_negative_rate
        for comparison_record in comparisons
        if comparison_record.projected_point_reconstruction_false_negative_rate is not None
    ]
    mean_projected_point_reconstruction_fnr = (
        sum(projected_point_reconstruction_fnrs) / len(projected_point_reconstruction_fnrs)
        if projected_point_reconstruction_fnrs
        else None
    )
    raw_future_transition_forecast_fnrs = [
        comparison_record.raw_future_transition_forecast_false_negative_rate
        for comparison_record in comparisons
        if comparison_record.raw_future_transition_forecast_false_negative_rate is not None
    ]
    mean_raw_future_transition_forecast_fnr = (
        sum(raw_future_transition_forecast_fnrs) / len(raw_future_transition_forecast_fnrs)
        if raw_future_transition_forecast_fnrs
        else None
    )
    LOGGER.info(
        "prospective evaluation completed cutoffs=%s rows=%s mechanism_supported=%s",
        len(comparisons),
        len(records),
        certification_mechanism_supported,
    )
    return ProspectiveEvaluationReport(
        total_evaluations=len(records),
        mean_false_negative_rate=metrics.false_negative_rate,
        mean_certification_rate=metrics.certification_rate,
        static_chronological_false_negative_rate=static_chronological_metrics.false_negative_rate,
        early_horizon_fnr_reduction_percentage_points=early_horizon_fnr_reduction,
        clean_fnr_degradation_percentage_points=mean_clean_fnr_degradation,
        scientific_outcome=(
            ScientificOutcome.PASS
            if certification_mechanism_supported
            else ScientificOutcome.INSUFFICIENT_EVIDENCE
        ),
        matched_benign_subtraction_false_negative_rate=mean_matched_benign_subtraction_fnr,
        projected_point_reconstruction_false_negative_rate=mean_projected_point_reconstruction_fnr,
        raw_future_transition_forecast_false_negative_rate=mean_raw_future_transition_forecast_fnr,
        mean_true_positive_rate=metrics.true_positive_rate,
        mean_false_positive_rate=metrics.false_positive_rate,
        mean_abstention_rate=metrics.abstention_rate,
        pr_auc=metrics.pr_auc,
        roc_auc=metrics.roc_auc,
    )
