from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

from fedact.certification.certificate import ClientConstraint, L2Ball
from fedact.certification.dynamics import AbstentionReason
from fedact.certification.selection import (
    ClientInformationMatrix,
    MaliciousSupportCount,
    SelectionBudget,
    greedy_action_interval_contraction_selection,
    greedy_d_optimal,
    largest_sample_count_selection,
    random_selection,
    uniform_action_weights,
    weighted_action_width,
)
from fedact.config.models import StrictModel
from fedact.data.splits import CalendarMonth
from fedact.domain.types import (
    AblationIdentifier,
    BinaryLabel,
    ClientIdentifier,
    ClientIndex,
    ClientSelectionComparator,
    CorrelationCoefficient,
    DegradationValue,
    EigengapRatio,
    EmbeddingComponent,
    EvaluationCount,
    FamilyName,
    IntervalBound,
    MetricRate,
    MonthIndex,
    NormValue,
    RankDimension,
    RidgeLambda,
    SampleCount,
    SampleIdentifier,
    ScientificOutcome,
    SplitCutoffIdentity,
    ThresholdValue,
    UncertaintyRadius,
    ValidationFlag,
)
from fedact.experiments.registry import ExperimentRuntime
from fedact.learning.detector import DetectorHead
from fedact.learning.federation import ClientTrainingPopulation, train_federated_detector
from fedact.learning.representation import (
    DEFAULT_ENCODER_HIDDEN_DIMENSIONS,
    EMBEDDING_DIMENSION,
    RepresentationEncoder,
    TrainingObservation,
)

LOGGER = logging.getLogger(__name__)


def _experiment_directory(application: ExperimentRuntime, workflow: str) -> Path:
    return (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / workflow
    )


class _AblationMeasurement(StrictModel):
    ablation_name: AblationIdentifier
    baseline_false_negative_rate: MetricRate
    ablated_false_negative_rate: MetricRate


class _AblationArtifact(StrictModel):
    measurements: list[_AblationMeasurement]


class _ProspectiveCutoffComparisonRecord(StrictModel):
    cutoff_id: SplitCutoffIdentity
    certified_false_negative_rate: MetricRate | None = None
    ambiguous_false_negative_rate: MetricRate | None = None
    hardened_false_negative_rate: MetricRate | None = None
    static_chronological_false_negative_rate: MetricRate | None = None
    matched_benign_subtraction_false_negative_rate: MetricRate | None = None
    projected_point_reconstruction_false_negative_rate: MetricRate | None = None
    raw_future_transition_forecast_false_negative_rate: MetricRate | None = None
    reactive_drift_adaptation_false_negative_rate: MetricRate | None = None


class _ProspectiveCutoffComparisonArtifact(StrictModel):
    comparisons: list[_ProspectiveCutoffComparisonRecord]


class _CentralPatternCutoffRecord(StrictModel):
    cutoff_id: SplitCutoffIdentity
    certified_precision: MetricRate | None = None
    point_selected_precision: MetricRate | None = None
    matched_random_precision: MetricRate | None = None
    matched_random_match_quality_sufficient: ValidationFlag = False
    mean_certified_action_width: NormValue | None = None


class _CentralPatternArtifact(StrictModel):
    cutoffs: list[_CentralPatternCutoffRecord]
    rank_alignment_spearman_rho: CorrelationCoefficient | None = None


class _IdentificationCutoffRecord(StrictModel):
    cutoff: CalendarMonth
    cohort: FamilyName
    fitted: ValidationFlag
    abstention_reason: AbstentionReason | None = None
    selected_rank: RankDimension | None = None
    eigengap_ratio: EigengapRatio | None = None
    beta: UncertaintyRadius | None = None
    no_controls_beta: UncertaintyRadius | None = None
    one_matched_control_beta: UncertaintyRadius | None = None
    zero_subspace_term_beta: UncertaintyRadius | None = None
    zero_control_span_term_beta: UncertaintyRadius | None = None
    zero_private_term_beta: UncertaintyRadius | None = None


class _IdentificationDiagnosticsArtifact(StrictModel):
    cohort: FamilyName
    cutoffs: list[_IdentificationCutoffRecord]


HARDENING_OFF_ABLATION_NAME: AblationIdentifier = "hardening_off"
POINT_VS_SET_ABLATION_NAME: AblationIdentifier = "point_vs_set"
NO_CONTROLS_ABLATION_NAME: AblationIdentifier = "no_controls"
ONE_MATCHED_CONTROL_ABLATION_NAME: AblationIdentifier = "one_matched_control"
ZERO_SUBSPACE_TERM_ABLATION_NAME: AblationIdentifier = "zero_subspace_uncertainty_term"
ZERO_CONTROL_SPAN_TERM_ABLATION_NAME: AblationIdentifier = "zero_control_span_allowance_term"
ZERO_PRIVATE_TERM_ABLATION_NAME: AblationIdentifier = "zero_private_transition_allowance_term"
SHUFFLED_HISTORY_ABLATION_NAME: AblationIdentifier = "shuffled_history"
NO_CHANGE_DYNAMICS_ABLATION_NAME: AblationIdentifier = "no_change_dynamics"


@dataclass(frozen=True)
class AblationResult:
    ablation_name: AblationIdentifier
    degradation_percentage_points: DegradationValue
    measured: ValidationFlag


@dataclass(frozen=True)
class AblationExperimentReport:
    ablations_evaluated: EvaluationCount
    results: tuple[AblationResult, ...]
    scientific_outcome: ScientificOutcome

    @property
    def evaluated_configurations(self) -> EvaluationCount:
        return self.ablations_evaluated


def _hardening_off_ablation_result(application: ExperimentRuntime) -> AblationResult | None:
    source = (
        _experiment_directory(application, "prospective-evaluation") / "cutoff-comparisons.json"
    )
    if not source.is_file():
        return None
    artifact = _ProspectiveCutoffComparisonArtifact.model_validate_json(
        source.read_text(encoding="utf-8")
    )
    paired = [
        (
            comparison.hardened_false_negative_rate,
            comparison.static_chronological_false_negative_rate,
        )
        for comparison in artifact.comparisons
        if comparison.hardened_false_negative_rate is not None
        and comparison.static_chronological_false_negative_rate is not None
    ]
    if not paired:
        return None
    mean_hardened = sum(hardened for hardened, _unhardened in paired) / len(paired)
    mean_unhardened = sum(unhardened for _hardened, unhardened in paired) / len(paired)
    return AblationResult(
        ablation_name=HARDENING_OFF_ABLATION_NAME,
        degradation_percentage_points=100.0 * (mean_unhardened - mean_hardened),
        measured=True,
    )


def _point_vs_set_ablation_result(application: ExperimentRuntime) -> AblationResult | None:
    source = (
        _experiment_directory(application, "action-certificate-validation") / "central-pattern.json"
    )
    if not source.is_file():
        return None
    artifact = _CentralPatternArtifact.model_validate_json(source.read_text(encoding="utf-8"))
    paired = [
        (cutoff.certified_precision, cutoff.point_selected_precision)
        for cutoff in artifact.cutoffs
        if cutoff.certified_precision is not None and cutoff.point_selected_precision is not None
    ]
    if not paired:
        return None
    mean_certified_precision = sum(certified for certified, _point in paired) / len(paired)
    mean_point_precision = sum(point for _certified, point in paired) / len(paired)
    return AblationResult(
        ablation_name=POINT_VS_SET_ABLATION_NAME,
        degradation_percentage_points=100.0 * (mean_certified_precision - mean_point_precision),
        measured=True,
    )


def _identification_diagnostics_artifact(
    application: ExperimentRuntime,
) -> _IdentificationDiagnosticsArtifact | None:
    source = (
        _experiment_directory(application, "prospective-evaluation")
        / "identification-diagnostics.json"
    )
    if not source.is_file():
        return None
    return _IdentificationDiagnosticsArtifact.model_validate_json(
        source.read_text(encoding="utf-8")
    )


def _beta_widening_ablation_result(
    application: ExperimentRuntime,
    ablation_name: AblationIdentifier,
    ablated_beta: Callable[[_IdentificationCutoffRecord], UncertaintyRadius | None],
) -> AblationResult | None:
    artifact = _identification_diagnostics_artifact(application)
    if artifact is None:
        return None
    paired: list[tuple[UncertaintyRadius, UncertaintyRadius]] = []
    for cutoff in artifact.cutoffs:
        ablated_value = ablated_beta(cutoff)
        if cutoff.beta is not None and ablated_value is not None:
            paired.append((cutoff.beta, ablated_value))
    if not paired:
        return None
    mean_beta = sum(beta for beta, _ablated in paired) / len(paired)
    mean_ablated_beta = sum(ablated for _beta, ablated in paired) / len(paired)
    return AblationResult(
        ablation_name=ablation_name,
        degradation_percentage_points=100.0 * (mean_ablated_beta - mean_beta),
        measured=True,
    )


def _no_controls_ablation_result(application: ExperimentRuntime) -> AblationResult | None:
    return _beta_widening_ablation_result(
        application, NO_CONTROLS_ABLATION_NAME, lambda cutoff: cutoff.no_controls_beta
    )


def _one_matched_control_ablation_result(application: ExperimentRuntime) -> AblationResult | None:
    return _beta_widening_ablation_result(
        application,
        ONE_MATCHED_CONTROL_ABLATION_NAME,
        lambda cutoff: cutoff.one_matched_control_beta,
    )


def _zero_subspace_term_ablation_result(application: ExperimentRuntime) -> AblationResult | None:
    return _beta_widening_ablation_result(
        application,
        ZERO_SUBSPACE_TERM_ABLATION_NAME,
        lambda cutoff: cutoff.zero_subspace_term_beta,
    )


def _zero_control_span_term_ablation_result(
    application: ExperimentRuntime,
) -> AblationResult | None:
    return _beta_widening_ablation_result(
        application,
        ZERO_CONTROL_SPAN_TERM_ABLATION_NAME,
        lambda cutoff: cutoff.zero_control_span_term_beta,
    )


def _zero_private_term_ablation_result(application: ExperimentRuntime) -> AblationResult | None:
    return _beta_widening_ablation_result(
        application,
        ZERO_PRIVATE_TERM_ABLATION_NAME,
        lambda cutoff: cutoff.zero_private_term_beta,
    )


class _TemporalDynamicsAblationRecord(StrictModel):
    endpoints_used: EvaluationCount
    baseline_coefficient: ThresholdValue
    baseline_process_error: IntervalBound
    shuffled_history_process_error: IntervalBound | None = None
    no_change_dynamics_process_error: IntervalBound | None = None


def _temporal_dynamics_ablation_results(
    application: ExperimentRuntime,
) -> tuple[AblationResult | None, AblationResult | None]:
    source = _experiment_directory(application, "ablations") / "temporal-dynamics.json"
    if not source.is_file():
        return None, None
    record = _TemporalDynamicsAblationRecord.model_validate_json(source.read_text(encoding="utf-8"))
    shuffled = None
    if record.shuffled_history_process_error is not None:
        shuffled = AblationResult(
            ablation_name=SHUFFLED_HISTORY_ABLATION_NAME,
            degradation_percentage_points=100.0
            * (record.shuffled_history_process_error - record.baseline_process_error),
            measured=True,
        )
    no_change = None
    if record.no_change_dynamics_process_error is not None:
        no_change = AblationResult(
            ablation_name=NO_CHANGE_DYNAMICS_ABLATION_NAME,
            degradation_percentage_points=100.0
            * (record.no_change_dynamics_process_error - record.baseline_process_error),
            measured=True,
        )
    return shuffled, no_change


def run_novelty_critical_ablations(application: ExperimentRuntime) -> AblationExperimentReport:
    results: list[AblationResult] = []
    real_ablation_names = frozenset(
        {
            HARDENING_OFF_ABLATION_NAME,
            POINT_VS_SET_ABLATION_NAME,
            NO_CONTROLS_ABLATION_NAME,
            ONE_MATCHED_CONTROL_ABLATION_NAME,
            ZERO_SUBSPACE_TERM_ABLATION_NAME,
            ZERO_CONTROL_SPAN_TERM_ABLATION_NAME,
            ZERO_PRIVATE_TERM_ABLATION_NAME,
            SHUFFLED_HISTORY_ABLATION_NAME,
            NO_CHANGE_DYNAMICS_ABLATION_NAME,
        }
    )
    hardening_off = _hardening_off_ablation_result(application)
    if hardening_off is not None:
        results.append(hardening_off)
    point_vs_set = _point_vs_set_ablation_result(application)
    if point_vs_set is not None:
        results.append(point_vs_set)
    no_controls = _no_controls_ablation_result(application)
    if no_controls is not None:
        results.append(no_controls)
    one_matched_control = _one_matched_control_ablation_result(application)
    if one_matched_control is not None:
        results.append(one_matched_control)
    for descriptive_result in (
        _zero_subspace_term_ablation_result(application),
        _zero_control_span_term_ablation_result(application),
        _zero_private_term_ablation_result(application),
        *_temporal_dynamics_ablation_results(application),
    ):
        if descriptive_result is not None:
            results.append(descriptive_result)
    source = _experiment_directory(application, "ablations") / "measurements.json"
    if source.is_file():
        artifact = _AblationArtifact.model_validate_json(source.read_text(encoding="utf-8"))
        results.extend(
            AblationResult(
                ablation_name=measurement.ablation_name,
                degradation_percentage_points=100.0
                * (
                    measurement.ablated_false_negative_rate
                    - measurement.baseline_false_negative_rate
                ),
                measured=True,
            )
            for measurement in artifact.measurements
            if measurement.ablation_name not in real_ablation_names
        )
    if not results:
        LOGGER.warning(
            "no ablation evidence is available: %s has no completed prospective-evaluation "
            "cutoff comparisons and %s is missing",
            _experiment_directory(application, "prospective-evaluation")
            / "cutoff-comparisons.json",
            source,
        )
        return AblationExperimentReport(0, (), ScientificOutcome.INSUFFICIENT_EVIDENCE)
    real_results = [
        result
        for result in (hardening_off, point_vs_set, no_controls, one_matched_control)
        if result is not None
    ]
    novelty_critical_claims_supported = bool(real_results) and all(
        result.degradation_percentage_points > 0.0 for result in real_results
    )
    LOGGER.info(
        "novelty-critical ablations evaluated ablations=%s novelty_critical_claims_supported=%s",
        len(results),
        novelty_critical_claims_supported,
    )
    return AblationExperimentReport(
        len(results),
        tuple(results),
        ScientificOutcome.PASS
        if novelty_critical_claims_supported
        else ScientificOutcome.INSUFFICIENT_EVIDENCE,
    )


class _ClientObservations(StrictModel):
    client_id: ClientIdentifier
    sample_ids: list[SampleIdentifier]
    features: list[list[EmbeddingComponent]]
    month_indices: list[MonthIndex]
    labels: list[BinaryLabel]
    historical_malicious_count: SampleCount = 0
    later_malicious_count: SampleCount = 0


class _FederationArtifact(StrictModel):
    clients: list[_ClientObservations]
    redundant_widths: list[IntervalBound] = []
    complementary_widths: list[IntervalBound] = []
    candidate_action_directions: list[list[EmbeddingComponent]] = []
    historical_plausibility_radius: IntervalBound | None = None


def _client_populations(artifact: _FederationArtifact) -> tuple[ClientTrainingPopulation, ...]:
    populations: list[ClientTrainingPopulation] = []
    for client in artifact.clients:
        lengths = {
            len(client.sample_ids),
            len(client.features),
            len(client.month_indices),
            len(client.labels),
        }
        if len(lengths) != 1 or not client.features:
            raise ValueError(f"federation client {client.client_id} has inconsistent observations")
        populations.append(
            ClientTrainingPopulation(
                client=client.client_id,
                observations=tuple(
                    TrainingObservation(sample_id, tuple(features), month, label)
                    for sample_id, features, month, label in zip(
                        client.sample_ids,
                        client.features,
                        client.month_indices,
                        client.labels,
                        strict=True,
                    )
                ),
            )
        )
    return tuple(populations)


def _information_matrices(
    populations: tuple[ClientTrainingPopulation, ...],
) -> tuple[ClientInformationMatrix, ...]:
    return tuple(
        ClientInformationMatrix(
            client=population.client,
            matrix=np.asarray(
                [tuple(obs.features) for obs in population.observations], dtype=float
            ).T
            @ np.asarray([tuple(obs.features) for obs in population.observations], dtype=float),
        )
        for population in populations
    )


def _information_matrix_radius(matrix: np.ndarray, ridge: RidgeLambda) -> float:
    eigenvalues = np.linalg.eigvalsh(matrix + ridge * np.eye(matrix.shape[0]))
    smallest = float(np.min(eigenvalues))
    if smallest <= 0.0:
        return float("inf")
    return 1.0 / float(np.sqrt(smallest))


@dataclass(frozen=True)
class ComparatorWidthReduction:
    comparator: ClientSelectionComparator
    total_reduction: IntervalBound
    mean_reduction_per_client: IntervalBound


@dataclass(frozen=True)
class SelectionExperimentReport:
    budget_fractions_tested: EvaluationCount
    d_optimal_superiority_verified: ValidationFlag
    comparator_reductions: tuple[ComparatorWidthReduction, ...]
    scientific_outcome: ScientificOutcome


def _weighted_width_reduction(
    action_directions: tuple[torch.Tensor, ...],
    action_weights: tuple[float, ...],
    plausibility_ball: L2Ball,
    constraints: tuple[ClientConstraint, ...],
    selected: tuple[ClientIndex, ...],
    vertices: SampleCount,
) -> IntervalBound:
    by_client = {constraint.client_index: constraint for constraint in constraints}
    empty_width = weighted_action_width(
        action_directions, action_weights, plausibility_ball, (), vertices
    )
    selected_width = weighted_action_width(
        action_directions,
        action_weights,
        plausibility_ball,
        tuple(by_client[client] for client in selected),
        vertices,
    )
    return empty_width - selected_width


def run_communication_limited_client_selection(
    application: ExperimentRuntime,
) -> SelectionExperimentReport:
    source = _experiment_directory(application, "federation") / "clients.json"
    if not source.is_file():
        LOGGER.warning(
            "client-selection input is missing: %s; natural client observations are required",
            source,
        )
        return SelectionExperimentReport(0, False, (), ScientificOutcome.INSUFFICIENT_EVIDENCE)
    artifact = _FederationArtifact.model_validate_json(source.read_text(encoding="utf-8"))
    populations = _client_populations(artifact)
    matrices = _information_matrices(populations)
    if len(matrices) < 2:
        LOGGER.warning("client-selection requires at least two eligible clients")
        return SelectionExperimentReport(0, False, (), ScientificOutcome.INSUFFICIENT_EVIDENCE)
    if not artifact.candidate_action_directions or artifact.historical_plausibility_radius is None:
        LOGGER.warning(
            "client-selection requires candidate action directions and a historical "
            "plausibility radius; workflow is ABSTENTION_EXPECTED without them"
        )
        return SelectionExperimentReport(0, False, (), ScientificOutcome.INSUFFICIENT_EVIDENCE)
    config = application.configuration.values.client_selection
    seeds = application.configuration.values.seeds.client_selection

    ordered_clients = tuple(matrix.client for matrix in matrices)
    client_index_by_identifier: dict[ClientIdentifier, ClientIndex] = {
        identifier: position for position, identifier in enumerate(ordered_clients)
    }
    by_client_matrix = {matrix.client: matrix.matrix for matrix in matrices}
    constraints = tuple(
        ClientConstraint(
            client_index=client_index_by_identifier[identifier],
            uncertainty_radius=_information_matrix_radius(
                by_client_matrix[identifier], config.d_optimal_ridge
            ),
            beta=0.0,
        )
        for identifier in ordered_clients
    )
    action_directions = tuple(
        torch.tensor(direction, dtype=torch.float32)
        for direction in artifact.candidate_action_directions
    )
    action_weights = uniform_action_weights(len(action_directions))
    dimension = action_directions[0].shape[0]
    plausibility_ball = L2Ball(
        center=np.zeros(dimension), radius=artifact.historical_plausibility_radius
    )
    malicious_supports = tuple(
        MaliciousSupportCount(
            client=population.client,
            historical_malicious_count=next(
                client.historical_malicious_count
                for client in artifact.clients
                if client.client_id == population.client
            ),
            later_malicious_count=next(
                client.later_malicious_count
                for client in artifact.clients
                if client.client_id == population.client
            ),
        )
        for population in populations
    )

    episodes_by_comparator: dict[ClientSelectionComparator, list[tuple[float, int]]] = {
        comparator: [] for comparator in ClientSelectionComparator
    }
    verified: list[bool] = []
    for fraction in config.budget_fractions:
        budget = SelectionBudget(fraction, len(matrices))
        vertices = len(matrices)

        d_optimal_selected = greedy_d_optimal(matrices, config.d_optimal_ridge, budget)
        d_optimal_indices = tuple(
            client_index_by_identifier[client] for client in d_optimal_selected
        )
        d_optimal_width_reduction = _weighted_width_reduction(
            action_directions,
            action_weights,
            plausibility_ball,
            constraints,
            d_optimal_indices,
            vertices,
        )
        episodes_by_comparator[ClientSelectionComparator.GLOBAL_INFORMATION].append(
            (d_optimal_width_reduction, len(d_optimal_indices))
        )

        largest_selected = largest_sample_count_selection(malicious_supports, budget)
        largest_indices = tuple(client_index_by_identifier[client] for client in largest_selected)
        largest_width_reduction = _weighted_width_reduction(
            action_directions,
            action_weights,
            plausibility_ball,
            constraints,
            largest_indices,
            vertices,
        )
        episodes_by_comparator[ClientSelectionComparator.LARGEST_SAMPLE_COUNT].append(
            (largest_width_reduction, len(largest_indices))
        )

        contraction_indices = greedy_action_interval_contraction_selection(
            action_directions, action_weights, constraints, plausibility_ball, budget, vertices
        )
        contraction_width_reduction = _weighted_width_reduction(
            action_directions,
            action_weights,
            plausibility_ball,
            constraints,
            contraction_indices,
            vertices,
        )
        episodes_by_comparator[ClientSelectionComparator.ACTION_INTERVAL_CONTRACTION].append(
            (contraction_width_reduction, len(contraction_indices))
        )

        random_reductions: list[float] = []
        for seed in seeds:
            random_selected = random_selection(ordered_clients, seed, budget)
            random_indices = tuple(client_index_by_identifier[client] for client in random_selected)
            random_reductions.append(
                _weighted_width_reduction(
                    action_directions,
                    action_weights,
                    plausibility_ball,
                    constraints,
                    random_indices,
                    vertices,
                )
            )
        mean_random_reduction = sum(random_reductions) / len(random_reductions)
        episodes_by_comparator[ClientSelectionComparator.RANDOM].append(
            (mean_random_reduction, budget.selected_count)
        )

        verified.append(
            d_optimal_width_reduction >= largest_width_reduction
            and d_optimal_width_reduction >= mean_random_reduction
        )
    comparator_reductions = tuple(
        ComparatorWidthReduction(
            comparator=comparator,
            total_reduction=sum(reduction for reduction, _count in episodes),
            mean_reduction_per_client=(
                sum(reduction / count for reduction, count in episodes) / len(episodes)
                if episodes
                else 0.0
            ),
        )
        for comparator, episodes in episodes_by_comparator.items()
    )
    return SelectionExperimentReport(
        len(verified),
        all(verified),
        comparator_reductions,
        ScientificOutcome.PASS if verified else ScientificOutcome.INSUFFICIENT_EVIDENCE,
    )


@dataclass(frozen=True)
class FederationGeometryReport:
    clients_evaluated: EvaluationCount
    delta_w_o: IntervalBound
    complementarity_verified: ValidationFlag
    scientific_outcome: ScientificOutcome
    geometries_tested: EvaluationCount = 0


def run_federation_geometry_evaluation(application: ExperimentRuntime) -> FederationGeometryReport:
    source = _experiment_directory(application, "federation") / "clients.json"
    if not source.is_file():
        LOGGER.warning(
            "federation input is missing: %s; an approved natural multi-client partition "
            "is required",
            source,
        )
        return FederationGeometryReport(0, 0.0, False, ScientificOutcome.INSUFFICIENT_EVIDENCE)
    artifact = _FederationArtifact.model_validate_json(source.read_text(encoding="utf-8"))
    populations = _client_populations(artifact)
    if len(populations) < 2:
        return FederationGeometryReport(0, 0.0, False, ScientificOutcome.INSUFFICIENT_EVIDENCE)
    feature_dimension = len(populations[0].observations[0].features)
    if any(
        len(observation.features) != feature_dimension
        for population in populations
        for observation in population.observations
    ):
        raise ValueError("federation clients must share a feature schema")
    config = application.configuration.values
    federated = train_federated_detector(
        RepresentationEncoder(
            feature_dimension, DEFAULT_ENCODER_HIDDEN_DIMENSIONS, EMBEDDING_DIMENSION
        ),
        DetectorHead(EMBEDDING_DIMENSION),
        populations,
        config.training.maximum_epochs,
        config.training.initial_learning_rate,
        config.training.final_learning_rate,
    )
    if federated.global_rounds_completed == 0:
        return FederationGeometryReport(
            len(populations), 0.0, False, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    redundant = np.asarray(artifact.redundant_widths, dtype=float)
    complementary = np.asarray(artifact.complementary_widths, dtype=float)
    if redundant.size == 0 or complementary.size == 0:
        raise ValueError("federation artifact must contain matched measured geometry widths")
    delta = interval_width_difference(redundant, complementary)
    return FederationGeometryReport(
        len(populations),
        delta,
        delta > 0.0,
        ScientificOutcome.PASS,
        len(config.synthetic.sweeps.federation.geometries),
    )


def select_clients_from_information(
    information_matrices: tuple[ClientInformationMatrix, ...],
    budget: SelectionBudget,
    ridge: RidgeLambda,
) -> tuple[ClientIdentifier, ...]:
    return greedy_d_optimal(information_matrices, ridge, budget)


def interval_width_difference(
    redundant_widths: np.ndarray, complementary_widths: np.ndarray
) -> IntervalBound:
    if redundant_widths.shape != complementary_widths.shape:
        raise ValueError("geometry comparisons require matched action units")
    return float(np.median(redundant_widths - complementary_widths))
