from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from fedact.certification.selection import (
    ClientInformationMatrix,
    SelectionBudget,
    greedy_d_optimal,
)
from fedact.config.models import StrictModel
from fedact.domain.types import (
    AblationIdentifier,
    BinaryLabel,
    ClientIdentifier,
    DegradationValue,
    EmbeddingComponent,
    EvaluationCount,
    IntervalBound,
    MetricRate,
    MonthIndex,
    RidgeLambda,
    SampleIdentifier,
    ScientificOutcome,
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


def _result_directory(application: ExperimentRuntime, workflow: str) -> Path:
    return (
        application.repository_root
        / application.configuration.values.workspace.directories.result_experiments
        / workflow
    )


class _AblationMeasurement(StrictModel):
    ablation_name: AblationIdentifier
    baseline_false_negative_rate: MetricRate
    ablated_false_negative_rate: MetricRate


class _AblationArtifact(StrictModel):
    measurements: list[_AblationMeasurement]


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


def run_novelty_critical_ablations(application: ExperimentRuntime) -> AblationExperimentReport:
    source = _result_directory(application, "ablations") / "measurements.json"
    if not source.is_file():
        LOGGER.warning(
            "ablation measurements are missing: %s; prospective evaluation must provide "
            "measured FNR pairs",
            source,
        )
        return AblationExperimentReport(0, (), ScientificOutcome.INSUFFICIENT_EVIDENCE)
    artifact = _AblationArtifact.model_validate_json(source.read_text(encoding="utf-8"))
    results = tuple(
        AblationResult(
            ablation_name=measurement.ablation_name,
            degradation_percentage_points=100.0
            * (measurement.ablated_false_negative_rate - measurement.baseline_false_negative_rate),
            measured=True,
        )
        for measurement in artifact.measurements
    )
    return AblationExperimentReport(
        len(results),
        results,
        ScientificOutcome.PASS if results else ScientificOutcome.INSUFFICIENT_EVIDENCE,
    )


class _ClientObservations(StrictModel):
    client_id: ClientIdentifier
    sample_ids: list[SampleIdentifier]
    features: list[list[EmbeddingComponent]]
    month_indices: list[MonthIndex]
    labels: list[BinaryLabel]


class _FederationArtifact(StrictModel):
    clients: list[_ClientObservations]
    redundant_widths: list[IntervalBound] = []
    complementary_widths: list[IntervalBound] = []


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


def _log_determinant(matrices: tuple[ClientInformationMatrix, ...], ridge: RidgeLambda) -> float:
    total = sum((matrix.matrix for matrix in matrices), start=np.zeros_like(matrices[0].matrix))
    sign, determinant = np.linalg.slogdet(total + ridge * np.eye(total.shape[0]))
    return float(determinant) if sign > 0 else float("-inf")


@dataclass(frozen=True)
class SelectionExperimentReport:
    budget_fractions_tested: EvaluationCount
    d_optimal_superiority_verified: ValidationFlag
    scientific_outcome: ScientificOutcome


def run_communication_limited_client_selection(
    application: ExperimentRuntime,
) -> SelectionExperimentReport:
    source = _result_directory(application, "federation") / "clients.json"
    if not source.is_file():
        LOGGER.warning(
            "client-selection input is missing: %s; natural client observations are required",
            source,
        )
        return SelectionExperimentReport(0, False, ScientificOutcome.INSUFFICIENT_EVIDENCE)
    populations = _client_populations(
        _FederationArtifact.model_validate_json(source.read_text(encoding="utf-8"))
    )
    matrices = _information_matrices(populations)
    if len(matrices) < 2:
        return SelectionExperimentReport(0, False, ScientificOutcome.INSUFFICIENT_EVIDENCE)
    config = application.configuration.values.client_selection
    verified: list[bool] = []
    by_client = {matrix.client: matrix for matrix in matrices}
    for fraction in config.budget_fractions:
        budget = SelectionBudget(fraction, len(matrices))
        selected = greedy_d_optimal(matrices, config.d_optimal_ridge, budget)
        selected_matrices = tuple(by_client[client] for client in selected)
        prefix = tuple(sorted(matrices, key=lambda item: item.client)[: budget.selected_count])
        verified.append(
            _log_determinant(selected_matrices, config.d_optimal_ridge)
            >= _log_determinant(prefix, config.d_optimal_ridge)
        )
    return SelectionExperimentReport(len(verified), all(verified), ScientificOutcome.PASS)


@dataclass(frozen=True)
class FederationGeometryReport:
    clients_evaluated: EvaluationCount
    delta_w_o: IntervalBound
    complementarity_verified: ValidationFlag
    scientific_outcome: ScientificOutcome
    geometries_tested: EvaluationCount = 0


def run_federation_geometry_evaluation(application: ExperimentRuntime) -> FederationGeometryReport:
    source = _result_directory(application, "federation") / "clients.json"
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
