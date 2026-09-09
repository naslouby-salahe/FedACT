from __future__ import annotations

import logging
import math
from dataclasses import dataclass, replace
from pathlib import Path

import torch

from fedact.certification.actions import ActionInterval
from fedact.certification.calibration import CalibrationCandidate
from fedact.certification.certificate import DomainValid, certify_action_interval
from fedact.certification.uncertainty import NuisanceEstimate
from fedact.config.models import CorruptedClientAllowanceParameters, StrictModel
from fedact.domain.types import (
    AngleDegrees,
    CertificationStatus,
    CorruptedClientAttack,
    DegradationValue,
    DetailMessage,
    EmbeddingComponent,
    EvaluationCount,
    IntervalBound,
    MetricRate,
    NormValue,
    SampleIdentifier,
    ScientificOutcome,
    ThresholdValue,
    ValidationFlag,
)
from fedact.experiments.registry import ExperimentRuntime
from fedact.learning.hardening import SampleChallengeSet, write_challenge_sets

LOGGER = logging.getLogger(__name__)


def _result_directory(application: ExperimentRuntime, workflow: str) -> Path:
    return (
        application.repository_root
        / application.configuration.values.workspace.directories.result_experiments
        / workflow
    )


class _ActionObservation(StrictModel):
    sample_id: SampleIdentifier
    lower_bound: IntervalBound
    upper_bound: IntervalBound
    domain_valid: ValidationFlag
    set_diameter: NormValue
    historical_diameter_quantile: ThresholdValue
    leave_one_client_out_passed: ValidationFlag = True
    challenge_embeddings: list[list[EmbeddingComponent]] = []


class _ActionArtifact(StrictModel):
    actions: list[_ActionObservation]


class _CalibrationObservation(StrictModel):
    candidate_id: DetailMessage
    tau_align: ThresholdValue
    tau_amb: ThresholdValue
    hardening_weight: ThresholdValue
    certified_positive: ValidationFlag
    covered: ValidationFlag
    clean_degradation_percentage_points: DegradationValue


class _CalibrationArtifact(StrictModel):
    observations: list[_CalibrationObservation]


class _StressMeasurement(StrictModel):
    scenario: DetailMessage
    boundary_reached: ValidationFlag
    completed: ValidationFlag


class _StressArtifact(StrictModel):
    measurements: list[_StressMeasurement]


@dataclass(frozen=True)
class ActionCertificateReport:
    total_actions: EvaluationCount
    certified_positive_count: EvaluationCount
    ambiguous_count: EvaluationCount
    abstention_count: EvaluationCount
    coverage_rate: MetricRate
    scientific_outcome: ScientificOutcome


def run_action_certificate_validation(application: ExperimentRuntime) -> ActionCertificateReport:
    source = _result_directory(application, "action-certificate-validation") / "actions.json"
    if not source.is_file():
        LOGGER.warning(
            "action-validation input is missing: %s; executed semantically valid operators "
            "are required",
            source,
        )
        return ActionCertificateReport(0, 0, 0, 0, 0.0, ScientificOutcome.INSUFFICIENT_EVIDENCE)
    artifact = _ActionArtifact.model_validate_json(source.read_text(encoding="utf-8"))
    config = application.configuration.values
    statuses: list[CertificationStatus] = []
    challenges: list[SampleChallengeSet] = []
    for action in artifact.actions:
        decision = certify_action_interval(
            action_interval=ActionInterval(action.lower_bound, action.upper_bound),
            domain_validity=DomainValid(action.domain_valid),
            alignment_threshold=config.certification.alignment_threshold.percentile_candidates[0]
            / 100.0,
            ambiguity_width_threshold=config.certification.ambiguity_width.percentile_candidates[-1]
            / 100.0,
            set_diameter=action.set_diameter,
            historical_realized_diameter_quantile=action.historical_diameter_quantile,
            leave_one_client_out_passed=action.leave_one_client_out_passed,
        )
        statuses.append(decision.status)
        if action.challenge_embeddings:
            challenges.append(
                SampleChallengeSet(
                    action.sample_id,
                    tuple(tuple(row) for row in action.challenge_embeddings),
                )
            )
    if challenges:
        write_challenge_sets(tuple(challenges), source.with_name("challenges.json"))
    total = len(statuses)
    certified = sum(status is CertificationStatus.CERTIFIED_POSITIVE for status in statuses)
    ambiguous = sum(status is CertificationStatus.AMBIGUOUS for status in statuses)
    abstentions = sum(status is CertificationStatus.ABSTAIN for status in statuses)
    return ActionCertificateReport(
        total,
        certified,
        ambiguous,
        abstentions,
        certified / total if total else 0.0,
        ScientificOutcome.PASS if total else ScientificOutcome.INSUFFICIENT_EVIDENCE,
    )


def run_nested_calibration(application: ExperimentRuntime) -> tuple[CalibrationCandidate, ...]:
    source = _result_directory(application, "nested-calibration") / "observations.json"
    if not source.is_file():
        LOGGER.warning(
            "nested-calibration input is missing: %s; pre-cutoff pseudo-future observations "
            "are required",
            source,
        )
        return ()
    artifact = _CalibrationArtifact.model_validate_json(source.read_text(encoding="utf-8"))
    grouped: dict[tuple[str, float, float, float], list[_CalibrationObservation]] = {}
    for observation in artifact.observations:
        grouped.setdefault(
            (
                observation.candidate_id,
                observation.tau_align,
                observation.tau_amb,
                observation.hardening_weight,
            ),
            [],
        ).append(observation)
    return tuple(
        CalibrationCandidate(
            candidate_id=candidate_id,
            tau_align=tau_align,
            tau_amb=tau_amb,
            hardening_weight=weight,
            observed_coverage=sum(row.covered for row in rows) / len(rows),
            observed_certification_rate=sum(row.certified_positive for row in rows) / len(rows),
            clean_degradation=sum(row.clean_degradation_percentage_points for row in rows)
            / len(rows),
        )
        for (candidate_id, tau_align, tau_amb, weight), rows in sorted(grouped.items())
    )


@dataclass(frozen=True)
class BoundaryStressReport:
    stress_sweeps_completed: EvaluationCount
    failure_boundaries_characterized: ValidationFlag
    scientific_outcome: ScientificOutcome
    boundary_points_tested: EvaluationCount = 0


def _rotate_subspace(subspace: torch.Tensor, degrees: AngleDegrees) -> torch.Tensor:
    if subspace.numel() == 0 or subspace.shape[0] < 2:
        return subspace
    theta = math.radians(degrees)
    rotation = torch.eye(subspace.shape[0], dtype=subspace.dtype, device=subspace.device)
    rotation[0, 0], rotation[0, 1] = math.cos(theta), -math.sin(theta)
    rotation[1, 0], rotation[1, 1] = math.sin(theta), math.cos(theta)
    return rotation @ subspace


def apply_corrupted_client_attack(
    estimate: NuisanceEstimate,
    attack: CorruptedClientAttack,
    parameters: CorruptedClientAllowanceParameters,
) -> NuisanceEstimate:
    if attack is CorruptedClientAttack.BASIS_ROTATION:
        return replace(
            estimate,
            subspace=_rotate_subspace(estimate.subspace, parameters.basis_rotation_degrees),
        )
    if attack is CorruptedClientAttack.FABRICATED_COMPLEMENTARITY:
        return replace(
            estimate,
            subspace=_rotate_subspace(
                estimate.subspace, parameters.fabricated_complementarity_rotation_degrees
            ),
        )
    if attack is CorruptedClientAttack.FALSE_RANK_REPORTING:
        return replace(
            estimate, selected_rank=estimate.selected_rank + parameters.false_rank_increment
        )
    if attack is CorruptedClientAttack.BETA_UNDER_REPORTING:
        return replace(
            estimate, uncertainty_radius=estimate.uncertainty_radius * parameters.beta_multiplier
        )
    return estimate


def run_robustness_and_failure_boundaries(application: ExperimentRuntime) -> BoundaryStressReport:
    source = _result_directory(application, "failure-boundaries") / "stress-measurements.json"
    if not source.is_file():
        LOGGER.warning(
            "failure-boundary input is missing: %s; completed real stress measurements are "
            "required",
            source,
        )
        return BoundaryStressReport(0, False, ScientificOutcome.INSUFFICIENT_EVIDENCE)
    artifact = _StressArtifact.model_validate_json(source.read_text(encoding="utf-8"))
    completed = [measurement for measurement in artifact.measurements if measurement.completed]
    boundaries = sum(measurement.boundary_reached for measurement in completed)
    return BoundaryStressReport(
        len(completed),
        bool(completed) and boundaries == len(completed),
        ScientificOutcome.PASS if completed else ScientificOutcome.INSUFFICIENT_EVIDENCE,
        boundaries,
    )
