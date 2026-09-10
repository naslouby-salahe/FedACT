from __future__ import annotations

import logging
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol, cast

import numpy as np
import torch
from scipy import stats as scipy_stats

from fedact.certification.actions import ActionInterval
from fedact.certification.calibration import (
    CalibrationCandidate,
    CalibrationSelectionError,
    select_best_calibration_candidate,
)
from fedact.certification.certificate import DomainValid, certify_action_interval
from fedact.certification.uncertainty import NuisanceEstimate
from fedact.config.models import CorruptedClientAllowanceParameters, StrictModel
from fedact.domain.types import (
    ActionCount,
    AngleDegrees,
    CertificationStatus,
    CohortIdentifier,
    CoordinateValue,
    CorrelationCoefficient,
    CorruptedClientAttack,
    DegradationValue,
    DetailMessage,
    EmbeddingComponent,
    EvaluationCount,
    HorizonStep,
    IntervalBound,
    MetricRate,
    NormValue,
    PValue,
    RandomMatchLevel,
    SampleIdentifier,
    ScientificOutcome,
    SeedValue,
    SplitCutoffIdentity,
    ThresholdValue,
    ValidationFlag,
)
from fedact.experiments.identification import (
    run_lamda_sparse_control_stress,
    run_lamda_weak_eigengap_stress,
)
from fedact.experiments.registry import ExperimentRuntime
from fedact.learning.hardening import SampleChallengeSet, write_challenge_sets

LOGGER = logging.getLogger(__name__)


class SpearmanResult(Protocol):
    statistic: CorrelationCoefficient
    pvalue: PValue


def _experiment_directory(application: ExperimentRuntime, workflow: str) -> Path:
    return (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
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
    cutoff_id: SplitCutoffIdentity
    cohort: CohortIdentifier
    horizon_step: HorizonStep
    source_sample_id: SampleIdentifier
    action_count: ActionCount
    point_score: CoordinateValue
    later_real_alignment_score: CoordinateValue


class _ActionArtifact(StrictModel):
    actions: list[_ActionObservation]


class _CentralPatternCutoffRecord(StrictModel):
    cutoff_id: SplitCutoffIdentity
    certified_precision: MetricRate | None
    point_selected_precision: MetricRate | None
    matched_random_precision: MetricRate | None
    matched_random_match_quality_sufficient: ValidationFlag


class _CentralPatternArtifact(StrictModel):
    cutoffs: list[_CentralPatternCutoffRecord]
    rank_alignment_spearman_rho: CorrelationCoefficient | None


class _CertificateDecisionRecord(StrictModel):
    sample_id: SampleIdentifier
    status: CertificationStatus


class _CertificateDecisionArtifact(StrictModel):
    decisions: list[_CertificateDecisionRecord]


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


class _SelectedCalibrationArtifact(StrictModel):
    candidate_id: DetailMessage
    tau_align: ThresholdValue
    tau_amb: ThresholdValue
    hardening_weight: ThresholdValue


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
    central_pattern_supported: ValidationFlag
    rank_alignment_spearman_rho: CorrelationCoefficient | None
    scientific_outcome: ScientificOutcome


_RANDOM_MATCH_LEVEL_PRIORITY = (
    RandomMatchLevel.EXACT,
    RandomMatchLevel.SOURCE_SAMPLE,
    RandomMatchLevel.COHORT_ONLY,
)
_RANDOM_MATCH_LEVELS_COUNTING_TOWARD_MINIMUM_FRACTION = (
    RandomMatchLevel.EXACT,
    RandomMatchLevel.SOURCE_SAMPLE,
)


def _match_key(action: _ActionObservation, level: RandomMatchLevel) -> tuple[object, ...]:
    if level is RandomMatchLevel.EXACT:
        return (
            action.cutoff_id,
            action.cohort,
            action.horizon_step,
            action.source_sample_id,
            action.action_count,
        )
    if level is RandomMatchLevel.SOURCE_SAMPLE:
        return (action.cutoff_id, action.cohort, action.horizon_step, action.source_sample_id)
    return (action.cutoff_id, action.cohort, action.horizon_step)


@dataclass(frozen=True)
class _MatchedRandomDraw:
    action: _ActionObservation
    match_level: RandomMatchLevel


def _sample_matched_random_valid(
    certified_actions: tuple[_ActionObservation, ...],
    valid_pool: tuple[_ActionObservation, ...],
    seed: SeedValue,
) -> tuple[_MatchedRandomDraw, ...]:
    rng = np.random.default_rng(seed)
    remaining = list(valid_pool)
    draws: list[_MatchedRandomDraw] = []
    for certified in certified_actions:
        for level in _RANDOM_MATCH_LEVEL_PRIORITY:
            key = _match_key(certified, level)
            candidates = [action for action in remaining if _match_key(action, level) == key]
            if candidates:
                index = int(rng.integers(len(candidates)))
                selected_candidate = candidates[index]
                remaining.remove(selected_candidate)
                draws.append(_MatchedRandomDraw(selected_candidate, level))
                break
    return tuple(draws)


def _later_real_precision(
    actions: tuple[_ActionObservation, ...], tau_align: ThresholdValue
) -> MetricRate | None:
    if not actions:
        return None
    return sum(action.later_real_alignment_score >= tau_align for action in actions) / len(actions)


def _compute_central_pattern(
    actions: tuple[_ActionObservation, ...],
    statuses_by_sample: dict[SampleIdentifier, CertificationStatus],
    selected: _SelectedCalibrationArtifact,
    operator_seeds: tuple[SeedValue, ...],
    minimum_exact_or_source_fraction: MetricRate,
) -> _CentralPatternArtifact:
    by_cutoff: dict[SplitCutoffIdentity, list[_ActionObservation]] = {}
    for action in actions:
        by_cutoff.setdefault(action.cutoff_id, []).append(action)
    records: list[_CentralPatternCutoffRecord] = []
    for cutoff_id in sorted(by_cutoff):
        group = tuple(by_cutoff[cutoff_id])
        certified_actions = tuple(
            action
            for action in group
            if statuses_by_sample[action.sample_id] is CertificationStatus.CERTIFIED_POSITIVE
        )
        valid_pool = tuple(action for action in group if action.domain_valid)
        certified_count = len(certified_actions)
        certified_precision = _later_real_precision(certified_actions, selected.tau_align)
        point_precision: MetricRate | None = None
        if certified_count > 0:
            ranked = sorted(valid_pool, key=lambda action: (-action.point_score, action.sample_id))
            point_precision = _later_real_precision(
                tuple(ranked[:certified_count]), selected.tau_align
            )
        random_precisions: list[MetricRate] = []
        match_fractions: list[float] = []
        for seed in operator_seeds:
            draws = _sample_matched_random_valid(certified_actions, valid_pool, seed)
            if not draws:
                continue
            precision = _later_real_precision(
                tuple(draw.action for draw in draws), selected.tau_align
            )
            if precision is not None:
                random_precisions.append(precision)
            match_fractions.append(
                sum(
                    draw.match_level in _RANDOM_MATCH_LEVELS_COUNTING_TOWARD_MINIMUM_FRACTION
                    for draw in draws
                )
                / len(draws)
            )
        match_quality_sufficient = (
            bool(match_fractions)
            and (sum(match_fractions) / len(match_fractions)) >= minimum_exact_or_source_fraction
        )
        records.append(
            _CentralPatternCutoffRecord(
                cutoff_id=cutoff_id,
                certified_precision=certified_precision,
                point_selected_precision=point_precision,
                matched_random_precision=(
                    sum(random_precisions) / len(random_precisions)
                    if random_precisions and match_quality_sufficient
                    else None
                ),
                matched_random_match_quality_sufficient=match_quality_sufficient,
            )
        )
    valid_actions = tuple(action for action in actions if action.domain_valid)
    rho: CorrelationCoefficient | None = None
    if len(valid_actions) >= 2:
        result = cast(
            SpearmanResult,
            scipy_stats.spearmanr(
                [action.lower_bound for action in valid_actions],
                [action.later_real_alignment_score for action in valid_actions],
            ),
        )
        candidate_rho = float(result.statistic)
        if math.isfinite(candidate_rho):
            rho = candidate_rho
    return _CentralPatternArtifact(cutoffs=records, rank_alignment_spearman_rho=rho)


def _central_pattern_supported(artifact: _CentralPatternArtifact) -> ValidationFlag:
    complete: list[tuple[MetricRate, MetricRate, MetricRate]] = []
    for record in artifact.cutoffs:
        certified = record.certified_precision
        point_selected = record.point_selected_precision
        matched_random = record.matched_random_precision
        if certified is not None and point_selected is not None and matched_random is not None:
            complete.append((certified, point_selected, matched_random))
    if not complete:
        return False
    mean_certified = sum(row[0] for row in complete) / len(complete)
    mean_point = sum(row[1] for row in complete) / len(complete)
    mean_random = sum(row[2] for row in complete) / len(complete)
    return mean_certified > mean_point > mean_random


def run_action_certificate_validation(application: ExperimentRuntime) -> ActionCertificateReport:
    source = _experiment_directory(application, "action-certificate-validation") / "actions.json"
    calibration_source = _experiment_directory(application, "nested-calibration") / "selected.json"
    if not source.is_file():
        LOGGER.warning(
            "action-validation input is missing: %s; executed semantically valid operators "
            "are required",
            source,
        )
        return ActionCertificateReport(
            0, 0, 0, 0, 0.0, False, None, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    if not calibration_source.is_file():
        LOGGER.warning(
            "action validation requires selected nested calibration: %s", calibration_source
        )
        return ActionCertificateReport(
            0, 0, 0, 0, 0.0, False, None, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    artifact = _ActionArtifact.model_validate_json(source.read_text(encoding="utf-8"))
    selected = _SelectedCalibrationArtifact.model_validate_json(
        calibration_source.read_text(encoding="utf-8")
    )
    statuses: list[CertificationStatus] = []
    statuses_by_sample: dict[SampleIdentifier, CertificationStatus] = {}
    decisions: list[_CertificateDecisionRecord] = []
    challenges: list[SampleChallengeSet] = []
    for action in artifact.actions:
        decision = certify_action_interval(
            action_interval=ActionInterval(action.lower_bound, action.upper_bound),
            domain_validity=DomainValid(action.domain_valid),
            alignment_threshold=selected.tau_align,
            ambiguity_width_threshold=selected.tau_amb,
            set_diameter=action.set_diameter,
            historical_realized_diameter_quantile=action.historical_diameter_quantile,
            leave_one_client_out_passed=action.leave_one_client_out_passed,
        )
        statuses.append(decision.status)
        statuses_by_sample[action.sample_id] = decision.status
        decisions.append(
            _CertificateDecisionRecord(sample_id=action.sample_id, status=decision.status)
        )
        if action.challenge_embeddings:
            challenges.append(
                SampleChallengeSet(
                    action.sample_id,
                    tuple(tuple(row) for row in action.challenge_embeddings),
                )
            )
    if challenges:
        write_challenge_sets(tuple(challenges), source.with_name("challenges.json"))
    decision_destination = source.with_name("certificate-decisions.json")
    decision_destination.parent.mkdir(parents=True, exist_ok=True)
    decision_destination.write_text(
        _CertificateDecisionArtifact(decisions=decisions).model_dump_json(indent=2),
        encoding="utf-8",
    )
    config = application.configuration.values
    central_pattern = _compute_central_pattern(
        tuple(artifact.actions),
        statuses_by_sample,
        selected,
        tuple(config.seeds.operator),
        config.certification.random_matching.minimum_exact_or_source_fraction,
    )
    central_pattern_destination = source.with_name("central-pattern.json")
    central_pattern_destination.write_text(
        central_pattern.model_dump_json(indent=2), encoding="utf-8"
    )
    central_pattern_supported = _central_pattern_supported(central_pattern)
    LOGGER.info(
        "action-certificate central pattern computed cutoffs=%s central_pattern_supported=%s "
        "rank_alignment_spearman_rho=%s",
        len(central_pattern.cutoffs),
        central_pattern_supported,
        central_pattern.rank_alignment_spearman_rho,
    )
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
        central_pattern_supported,
        central_pattern.rank_alignment_spearman_rho,
        ScientificOutcome.PASS
        if central_pattern_supported
        else ScientificOutcome.INSUFFICIENT_EVIDENCE,
    )


def run_nested_calibration(application: ExperimentRuntime) -> tuple[CalibrationCandidate, ...]:
    source = _experiment_directory(application, "nested-calibration") / "observations.json"
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
    candidates = tuple(
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
    if not candidates:
        return ()
    config = application.configuration.values
    try:
        selected = select_best_calibration_candidate(
            candidates,
            config.identification.target_coverage.primary,
            config.hardening.weight.maximum_clean_fnr_degradation_percentage_points,
        ).selected_candidate
    except CalibrationSelectionError:
        LOGGER.warning("no nested calibration candidate meets configured validity requirements")
        return candidates
    selected_destination = (
        _experiment_directory(application, "nested-calibration") / "selected.json"
    )
    selected_destination.parent.mkdir(parents=True, exist_ok=True)
    selected_destination.write_text(
        _SelectedCalibrationArtifact(
            candidate_id=selected.candidate_id,
            tau_align=selected.tau_align,
            tau_amb=selected.tau_amb,
            hardening_weight=selected.hardening_weight,
        ).model_dump_json(indent=2),
        encoding="utf-8",
    )
    return candidates


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
    weak_eigengap = run_lamda_weak_eigengap_stress(application)
    weak_eigengap_completed = len(weak_eigengap.results)
    weak_eigengap_reached = sum(result.rank_destabilized for result in weak_eigengap.results)
    LOGGER.info(
        "weak-eigengap real stress endpoint=%s multipliers_tested=%s destabilized=%s",
        weak_eigengap.endpoint,
        weak_eigengap_completed,
        weak_eigengap_reached,
    )

    sparse_control = run_lamda_sparse_control_stress(application)
    sparse_control_completed = len(sparse_control.results)
    sparse_control_reached = sum(
        (not result.fitted) or (result.perturbed_beta or 0.0) > result.baseline_beta
        for result in sparse_control.results
    )
    LOGGER.info(
        "sparse-control real stress endpoint=%s fractions_tested=%s widened_or_abstained=%s",
        sparse_control.endpoint,
        sparse_control_completed,
        sparse_control_reached,
    )

    real_completed = weak_eigengap_completed + sparse_control_completed
    real_boundaries_reached = weak_eigengap_reached + sparse_control_reached

    source = _experiment_directory(application, "failure-boundaries") / "stress-measurements.json"
    if not source.is_file():
        LOGGER.warning(
            "failure-boundary input is missing: %s; completed real stress measurements are "
            "required",
            source,
        )
        if real_completed == 0:
            return BoundaryStressReport(0, False, ScientificOutcome.INSUFFICIENT_EVIDENCE)
        return BoundaryStressReport(
            real_completed,
            real_boundaries_reached == real_completed,
            (
                ScientificOutcome.PASS
                if real_boundaries_reached == real_completed
                else ScientificOutcome.INSUFFICIENT_EVIDENCE
            ),
            real_completed,
        )
    artifact = _StressArtifact.model_validate_json(source.read_text(encoding="utf-8"))
    external_completed = [
        measurement for measurement in artifact.measurements if measurement.completed
    ]
    external_boundaries = sum(measurement.boundary_reached for measurement in external_completed)
    total_completed = len(external_completed) + real_completed
    total_boundaries = external_boundaries + real_boundaries_reached
    return BoundaryStressReport(
        total_completed,
        total_completed > 0 and total_boundaries == total_completed,
        ScientificOutcome.PASS if total_completed > 0 else ScientificOutcome.INSUFFICIENT_EVIDENCE,
        total_boundaries,
    )
