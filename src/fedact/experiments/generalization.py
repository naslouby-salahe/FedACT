from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch

from fedact._vendor.transcendent.scores import compute_p_values_cred_and_conf
from fedact._vendor.transcendent.thresholding import (
    ClassThresholds,
    apply_threshold,
    get_performance_with_rejection,
)
from fedact.analysis.comparisons import CutoffAggregate
from fedact.analysis.metrics import EvaluationRecord, compute_evaluation_metrics
from fedact.certification.client_procedure import select_stable_nuisance_rank
from fedact.certification.dynamics import fit_scalar_model
from fedact.config.models import StrictModel
from fedact.data.splits import (
    calendar_month,
    confirmatory_outcome_for_cutoffs,
    earliest_complete_transition_endpoint,
    transition_windows,
    windowed_mean,
)
from fedact.domain.types import (
    BinaryLabel,
    CalendarMonth,
    CertificationStatus,
    CorrelationCoefficient,
    CoverageLevel,
    CutoffCount,
    DatasetSelector,
    DegradationValue,
    EvaluationCount,
    ExecutableWorkflowName,
    FamilyName,
    LossValue,
    MetricRate,
    ProbabilityValue,
    PValueCriterion,
    PValueSeries,
    SampleIdentifier,
    ScientificOutcome,
    SplitCutoffIdentity,
    ValidationFlag,
    WorkflowArtifactName,
)
from fedact.experiments.baselines import matched_benign_subtraction, projected_point_reconstruction
from fedact.experiments.ember2024_identification import Ember2024IdentificationDiagnosticsArtifact
from fedact.experiments.identification import IdentificationDiagnosticsArtifact
from fedact.experiments.lamda_population import (
    LamdaPopulation,
    eligible_cutoffs,
    load_lamda_population,
)
from fedact.experiments.registry import ExperimentRuntime
from fedact.learning.detector import DetectorHead, train_base_detector
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
    train_representation_encoder,
)
from fedact.learning.scoring import score_samples

LOGGER = logging.getLogger(__name__)

_NCM_DECISION_SCALE = 2.0
_NCM_DECISION_OFFSET = 1.0


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
    reactive_drift_adaptation_false_negative_rate: MetricRate | None = None


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
        / ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION
        / WorkflowArtifactName.CENTRAL_PATTERN
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
        / ExecutableWorkflowName.PROSPECTIVE_EVALUATION
        / WorkflowArtifactName.CUTOFF_COMPARISONS
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
    lamda_cutoffs_fitted: EvaluationCount
    ember2024_cutoffs_fitted: EvaluationCount
    mechanism_replicates: ValidationFlag
    ember2024_action_intervals_available: ValidationFlag
    paired_action_cutoffs: CutoffCount
    scientific_outcome: ScientificOutcome

    @property
    def generalization_valid(self) -> ValidationFlag:
        return self.mechanism_replicates and self.ember2024_action_intervals_available


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
    reactive_drift_adaptation_false_negative_rate: MetricRate | None = None
    mean_true_positive_rate: MetricRate | None = None
    mean_false_positive_rate: MetricRate | None = None
    mean_abstention_rate: MetricRate | None = None
    pr_auc: MetricRate | None = None
    roc_auc: MetricRate | None = None


def run_cross_corpus_generalization(application: ExperimentRuntime) -> CrossCorpusReport:
    experiments_root = (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / ExecutableWorkflowName.PROSPECTIVE_EVALUATION
    )
    lamda_path = experiments_root / WorkflowArtifactName.IDENTIFICATION_DIAGNOSTICS
    ember2024_path = experiments_root / "ember2024-identification-diagnostics.json"
    if not lamda_path.is_file() or not ember2024_path.is_file():
        LOGGER.warning(
            "cross-corpus generalization requires both corpora's own independent "
            "identification diagnostics to already exist: lamda=%s ember2024=%s",
            lamda_path.is_file(),
            ember2024_path.is_file(),
        )
        return CrossCorpusReport(0, 0, False, False, 0, ScientificOutcome.INSUFFICIENT_EVIDENCE)

    lamda_artifact = IdentificationDiagnosticsArtifact.model_validate_json(
        lamda_path.read_text(encoding="utf-8")
    )
    ember2024_artifact = Ember2024IdentificationDiagnosticsArtifact.model_validate_json(
        ember2024_path.read_text(encoding="utf-8")
    )
    lamda_cutoffs_fitted = sum(1 for cutoff in lamda_artifact.cutoffs if cutoff.fitted)
    ember2024_cutoffs_fitted = sum(1 for cutoff in ember2024_artifact.cutoffs if cutoff.fitted)
    mechanism_replicates = lamda_cutoffs_fitted > 0 and ember2024_cutoffs_fitted > 0

    LOGGER.warning(
        "ember2024 problem-space PE action generation has no authorized raw-PE "
        "acquisition route; every EMBER2024 sample is operator_ineligible, "
        "so paired action-interval evidence is structurally unavailable"
    )
    paired_action_cutoffs: CutoffCount = 0
    ember2024_action_intervals_available = False
    confirmatory_outcome = confirmatory_outcome_for_cutoffs(
        paired_action_cutoffs, application.configuration.values.statistics.minimum_paired_cutoffs
    )
    LOGGER.info(
        "cross-corpus generalization lamda_fitted=%s ember2024_fitted=%s "
        "mechanism_replicates=%s paired_action_cutoffs=%s outcome=%s",
        lamda_cutoffs_fitted,
        ember2024_cutoffs_fitted,
        mechanism_replicates,
        paired_action_cutoffs,
        confirmatory_outcome,
    )
    return CrossCorpusReport(
        lamda_cutoffs_fitted=lamda_cutoffs_fitted,
        ember2024_cutoffs_fitted=ember2024_cutoffs_fitted,
        mechanism_replicates=mechanism_replicates,
        ember2024_action_intervals_available=ember2024_action_intervals_available,
        paired_action_cutoffs=paired_action_cutoffs,
        scientific_outcome=confirmatory_outcome,
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
    reactive_drift_adaptation_false_negative_rate: MetricRate | None = None


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


def _reactive_drift_adaptation_ncm(probability: ProbabilityValue, label: bool) -> float:
    decision = _NCM_DECISION_SCALE * probability - _NCM_DECISION_OFFSET
    return -decision if label else decision


def _reactive_drift_adaptation_quartile_candidates(
    p_values: dict[PValueCriterion, PValueSeries],
    predicted_labels: np.ndarray,
    groundtruth_labels: np.ndarray,
) -> dict[str, dict[str, ClassThresholds]]:
    candidates: dict[str, dict[str, ClassThresholds]] = {}
    correct = predicted_labels == groundtruth_labels
    for key in (PValueCriterion("cred"), PValueCriterion("conf")):
        scores = np.asarray(p_values[key], dtype=np.float64)
        scores_malicious = scores[(predicted_labels == 1) & correct]
        scores_benign = scores[(predicted_labels == 0) & correct]
        if scores_malicious.size == 0 or scores_benign.size == 0:
            return {}
        for quartile_key, percentile in (("q1", 25.0), ("q2", 50.0), ("q3", 75.0), ("mean", None)):
            malicious_threshold = (
                float(np.percentile(scores_malicious, percentile))
                if percentile is not None
                else float(np.mean(scores_malicious))
            )
            benign_threshold = (
                float(np.percentile(scores_benign, percentile))
                if percentile is not None
                else float(np.mean(scores_benign))
            )
            candidates.setdefault(quartile_key, {})[key] = ClassThresholds(
                malicious=malicious_threshold,
                benign=benign_threshold,
            )
    return candidates


def _select_reactive_drift_adaptation_threshold(
    candidates: dict[str, dict[str, ClassThresholds]],
    validation_p_values: dict[PValueCriterion, PValueSeries],
    validation_groundtruth: np.ndarray,
    target_coverage: CoverageLevel,
    max_clean_degradation_points: DegradationValue,
) -> dict[str, ClassThresholds] | None:
    best_threshold: dict[str, ClassThresholds] | None = None
    best_certification_rate = -1.0
    best_clean_degradation = float("inf")
    for quartile_key in sorted(candidates):
        threshold = candidates[quartile_key]
        keep_mask = apply_threshold(
            threshold,
            {str(criterion): list(series) for criterion, series in validation_p_values.items()},
            validation_groundtruth,
        )
        performance = get_performance_with_rejection(
            validation_groundtruth, validation_groundtruth, keep_mask, full=False
        )
        coverage = performance["kept_pos_perc"]
        certification_rate = performance["kept_total_perc"]
        clean_degradation = performance["reject_neg_perc"] * 100.0
        if coverage < target_coverage or clean_degradation > max_clean_degradation_points:
            continue
        if certification_rate > best_certification_rate or (
            certification_rate == best_certification_rate
            and clean_degradation < best_clean_degradation
        ):
            best_threshold = threshold
            best_certification_rate = certification_rate
            best_clean_degradation = clean_degradation
    return best_threshold


def _reactive_drift_adaptation_false_negative_rate(
    application: ExperimentRuntime,
    validation: tuple[TrainingObservation, ...],
    encoder: RepresentationEncoder,
    detector: DetectorHead,
    later_scores: tuple[ProbabilityValue, ...],
    later_labels: np.ndarray,
) -> MetricRate | None:
    config = application.configuration.values
    if not validation:
        return None
    validation_groundtruth = np.fromiter(
        (int(obs.label) for obs in validation), dtype=np.int_, count=len(validation)
    )
    if (
        np.count_nonzero(validation_groundtruth) == 0
        or np.count_nonzero(validation_groundtruth == 0) == 0
    ):
        return None
    validation_features = torch.stack(
        [
            torch.tensor(obs.features, dtype=torch.float32)
            if isinstance(obs.features, tuple)
            else obs.features
            for obs in validation
        ]
    )
    validation_scored = score_samples(
        encoder,
        detector,
        tuple(obs.sample_id for obs in validation),
        validation_features,
    )
    validation_ncms = [
        _reactive_drift_adaptation_ncm(score.probability, bool(label))
        for score, label in zip(validation_scored, validation_groundtruth, strict=True)
    ]
    validation_groundtruth_list = [int(value) for value in validation_groundtruth]
    validation_p_values = {
        PValueCriterion(criterion): PValueSeries(series)
        for criterion, series in compute_p_values_cred_and_conf(
            validation_ncms,
            validation_groundtruth_list,
            validation_ncms,
            validation_groundtruth_list,
        ).items()
    }

    candidates = _reactive_drift_adaptation_quartile_candidates(
        validation_p_values, validation_groundtruth, validation_groundtruth
    )
    if not candidates:
        return None
    threshold = _select_reactive_drift_adaptation_threshold(
        candidates,
        validation_p_values,
        validation_groundtruth,
        config.identification.target_coverage.primary,
        config.hardening.weight.maximum_clean_fnr_degradation_percentage_points,
    )
    if threshold is None:
        return None
    later_predicted = np.fromiter(
        (int(score >= 0.5) for score in later_scores), dtype=np.int_, count=len(later_scores)
    )
    later_ncms = [
        _reactive_drift_adaptation_ncm(score, bool(label))
        for score, label in zip(later_scores, later_predicted, strict=True)
    ]
    later_p_values = compute_p_values_cred_and_conf(
        validation_ncms,
        validation_groundtruth_list,
        later_ncms,
        [int(value) for value in later_predicted],
    )
    keep_mask = apply_threshold(threshold, later_p_values, later_predicted)
    malicious_mask = later_labels.astype(bool)
    if not malicious_mask.any():
        return None
    later_scores_array = np.asarray(later_scores, dtype=np.float64)
    undetected_and_unflagged = malicious_mask & keep_mask & (later_scores_array < 0.5)
    return float(np.count_nonzero(undetected_and_unflagged) / np.count_nonzero(malicious_mask))


def _score_cutoff_population(
    application: ExperimentRuntime,
    population: LamdaPopulation,
    historical: np.ndarray,
    later: np.ndarray,
) -> _CutoffScoring | None:
    config = application.configuration.values
    observations = tuple(
        TrainingObservation(
            sample_id=sample_id,
            features=torch.from_numpy(feature),
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
        / ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION
        / WorkflowArtifactName.CHALLENGES
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
    later_labels = population.labels[later]
    reactive_drift_adaptation_fnr = _reactive_drift_adaptation_false_negative_rate(
        application,
        validation,
        encoder,
        detector,
        tuple(score.probability for score in scored),
        later_labels,
    )

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
        reactive_drift_adaptation_false_negative_rate=reactive_drift_adaptation_fnr,
    )


def run_prospective_fedact_evaluation(
    application: ExperimentRuntime,
) -> ProspectiveEvaluationReport:
    certificate_decisions = (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION
        / WorkflowArtifactName.CERTIFICATE_DECISIONS
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
    population = load_lamda_population(application)
    if population is None:
        return ProspectiveEvaluationReport(
            0, 0.0, 0.0, 0.0, 0.0, 0.0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    cutoffs = eligible_cutoffs(application, population)
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
                reactive_drift_adaptation_false_negative_rate=(
                    scored_population.reactive_drift_adaptation_false_negative_rate
                ),
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
        / ExecutableWorkflowName.PROSPECTIVE_EVALUATION
        / WorkflowArtifactName.CUTOFF_COMPARISONS
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
    reactive_drift_adaptation_fnrs = [
        comparison_record.reactive_drift_adaptation_false_negative_rate
        for comparison_record in comparisons
        if comparison_record.reactive_drift_adaptation_false_negative_rate is not None
    ]
    mean_reactive_drift_adaptation_fnr = (
        sum(reactive_drift_adaptation_fnrs) / len(reactive_drift_adaptation_fnrs)
        if reactive_drift_adaptation_fnrs
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
        reactive_drift_adaptation_false_negative_rate=mean_reactive_drift_adaptation_fnr,
        mean_true_positive_rate=metrics.true_positive_rate,
        mean_false_positive_rate=metrics.false_positive_rate,
        mean_abstention_rate=metrics.abstention_rate,
        pr_auc=metrics.pr_auc,
        roc_auc=metrics.roc_auc,
    )
