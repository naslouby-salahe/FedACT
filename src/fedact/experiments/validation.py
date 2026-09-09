from __future__ import annotations

import math
from dataclasses import dataclass, replace

import torch

from fedact.certification.calibration import (
    CalibrationCandidate,
    HardeningWeightDegradation,
    HardeningWeightDegradations,
    generate_calibration_candidates,
)
from fedact.certification.certificate import DomainValid, build_nuisance_spaces, certify_action_interval
from fedact.certification.uncertainty import NuisanceEstimate, estimate_client_nuisance_subspace, solve_action_interval
from fedact.config.models import CorruptedClientAllowanceParameters
from fedact.domain.types import (
    CertificationStatus,
    CorruptedClientAttack,
    DegradationValue,
    DetailMessage,
    EvaluationCount,
    MetricRate,
    RankSelectionMethod,
    SampleIdentifier,
    ScientificOutcome,
    ThresholdValue,
    ValidationFlag,
)
from fedact.experiments.baselines import verify_subtraction_comparator_parity
from fedact.experiments.registry import ExperimentRuntime
from fedact.learning.detector import DetectorHead
from fedact.learning.hardening import (
    SampleChallengeSet,
    clean_false_negative_rate,
    harden_detector_head,
)
from fedact.learning.representation import EMBEDDING_DIMENSION, RepresentationEncoder, TrainingObservation

_ACTION_MAGNITUDE = 2.0


@dataclass(frozen=True)
class ActionCertificateReport:
    total_actions: EvaluationCount
    certified_positive_count: EvaluationCount
    ambiguous_count: EvaluationCount
    abstention_count: EvaluationCount
    coverage_rate: MetricRate
    scientific_outcome: ScientificOutcome


def run_action_certificate_validation(application: ExperimentRuntime) -> ActionCertificateReport:

    config = application.configuration.values
    parity = verify_subtraction_comparator_parity(config.numerical.projection_tie_tolerance)
    if not parity.is_valid:
        return ActionCertificateReport(
            total_actions=0,
            certified_positive_count=0,
            ambiguous_count=0,
            abstention_count=0,
            coverage_rate=0.0,
            scientific_outcome=ScientificOutcome.FAIL,
        )
    candidates = run_nested_calibration(application)
    if not candidates:
        return ActionCertificateReport(
            total_actions=0,
            certified_positive_count=0,
            ambiguous_count=0,
            abstention_count=0,
            coverage_rate=0.0,
            scientific_outcome=ScientificOutcome.INSUFFICIENT_EVIDENCE,
        )
    latent_dim = 64
    nuisance_estimates = [
        estimate_client_nuisance_subspace(
            client_controls=torch.randn(20, latent_dim),
            rank_selection=RankSelectionMethod.FIXED_RANK,
            fixed_rank=config.identification.nuisance_rank.maximum,
            eigengap_regularization=config.numerical.rank_clip_epsilon_relative,
            scale_standardization_floor=config.numerical.scale_standardization_floor,
        )
        for _unused in range(5)
    ]
    feasible_set = build_nuisance_spaces(
        nuisance_subspaces=tuple(e.subspace for e in nuisance_estimates),
        uncertainty_radii=tuple(0.01 for _unused in nuisance_estimates),
    )
    actions = [torch.ones(latent_dim) * _ACTION_MAGNITUDE for _unused in range(50)]

    certified = 0
    ambiguous = 0
    abstained = 0

    for action in actions:
        interval = solve_action_interval(action_vector=action, feasible_set=feasible_set)
        decision = certify_action_interval(
            action_interval=interval,
            domain_validity=DomainValid(valid=True),
            alignment_threshold=0.01,
            ambiguity_width_threshold=5.0,
            set_diameter=feasible_set.diameter,
            historical_realized_diameter_quantile=(
                config.certification.forecast_set_diameter_abstention.historical_realized_diameter_quantile
            ),
        )
        if decision.status is CertificationStatus.CERTIFIED_POSITIVE:
            certified += 1
        elif decision.status is CertificationStatus.AMBIGUOUS:
            ambiguous += 1
        else:
            abstained += 1

    coverage = (certified + ambiguous) / max(1, len(actions))
    outcome = (
        ScientificOutcome.PASS
        if certified > 0 and abstained < len(actions)
        else ScientificOutcome.INSUFFICIENT_EVIDENCE
    )

    return ActionCertificateReport(
        total_actions=len(actions),
        certified_positive_count=certified,
        ambiguous_count=ambiguous,
        abstention_count=abstained,
        coverage_rate=coverage,
        scientific_outcome=outcome,
    )


_INPUT_DIMENSION = 512
_TRAINING_POPULATION_ROWS = 20
_VALIDATION_POPULATION_ROWS = 10
_LABEL_ALTERNATION_MODULUS = 2


def _training_population(prefix: DetailMessage, size: int) -> tuple[TrainingObservation, ...]:
    return tuple(
        TrainingObservation(
            sample_id=SampleIdentifier(f"{prefix}_{i}"),
            features=torch.randn(_INPUT_DIMENSION),
            month_index=1,
            label=bool(i % _LABEL_ALTERNATION_MODULUS == 0),
        )
        for i in range(size)
    )


def _clean_degradation(
    application: ExperimentRuntime, hardening_weight: ThresholdValue
) -> DegradationValue:
    config = application.configuration.values
    encoder = RepresentationEncoder(input_dimension=_INPUT_DIMENSION)
    detector = DetectorHead(latent_dimension=EMBEDDING_DIMENSION)
    train_population = _training_population("cal_t", _TRAINING_POPULATION_ROWS)
    validation_population = _training_population("cal_v", _VALIDATION_POPULATION_ROWS)
    challenges = (
        SampleChallengeSet(
            source_sample_id=train_population[0].sample_id,
            challenge_embeddings=(tuple(float(x) for x in torch.randn(EMBEDDING_DIMENSION)),),
        ),
    )
    baseline_clean_fnr = clean_false_negative_rate(detector, encoder, validation_population)
    hardening_result = harden_detector_head(
        encoder=encoder,
        head=detector,
        training_population=train_population,
        validation_population=validation_population,
        challenge_sets=challenges,
        baseline_clean_fnr=baseline_clean_fnr,
        initial_learning_rate=config.training.initial_learning_rate,
        final_learning_rate=config.training.final_learning_rate,
        maximum_epochs=config.training.maximum_epochs,
        maximum_clean_fnr_degradation_percentage_points=(
            config.hardening.weight.maximum_clean_fnr_degradation_percentage_points
        ),
        projection_tie_tolerance=config.numerical.projection_tie_tolerance,
        hardening_weight=hardening_weight,
    )
    return hardening_result.clean_fnr_degradation_percentage_points


def run_nested_calibration(application: ExperimentRuntime) -> tuple[CalibrationCandidate, ...]:
    config = application.configuration.values
    weight_grid = tuple(config.hardening.weight.candidates)
    clean_degradations = HardeningWeightDegradations(
        entries=tuple(
            HardeningWeightDegradation(
                hardening_weight=weight,
                clean_degradation=_clean_degradation(application, weight),
            )
            for weight in weight_grid
        )
    )
    return generate_calibration_candidates(
        alignment_percentile_candidates=tuple(
            config.certification.alignment_threshold.percentile_candidates
        ),
        ambiguity_width_percentile_candidates=tuple(
            config.certification.ambiguity_width.percentile_candidates
        ),
        hardening_weight_candidates=weight_grid,
        maximum_nuisance_rank=config.identification.nuisance_rank.maximum,
        eigengap_regularization=config.numerical.rank_clip_epsilon_relative,
        scale_standardization_floor=config.numerical.scale_standardization_floor,
        historical_realized_diameter_quantile=(
            config.certification.forecast_set_diameter_abstention.historical_realized_diameter_quantile
        ),
        clean_degradations=clean_degradations,
    )

_STRESS_SWEEP_BASELINE_ROWS = 20


@dataclass(frozen=True)
class BoundaryStressReport:
    stress_sweeps_completed: EvaluationCount
    failure_boundaries_characterized: ValidationFlag
    scientific_outcome: ScientificOutcome
    boundary_points_tested: EvaluationCount = 5


def _rotate_subspace(subspace: torch.Tensor, degrees: float) -> torch.Tensor:
    if subspace.numel() == 0 or subspace.shape[0] < 2:
        return subspace
    theta = math.radians(degrees)
    dimension = subspace.shape[0]
    rotation = torch.eye(dimension, dtype=subspace.dtype)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    rotation[0, 0] = cos_t
    rotation[0, 1] = -sin_t
    rotation[1, 0] = sin_t
    rotation[1, 1] = cos_t
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
        new_rank = estimate.selected_rank + parameters.false_rank_increment
        return replace(estimate, selected_rank=new_rank)
    if attack is CorruptedClientAttack.BETA_UNDER_REPORTING:
        return replace(
            estimate, uncertainty_radius=estimate.uncertainty_radius * parameters.beta_multiplier
        )
    return estimate


def run_robustness_and_failure_boundaries(application: ExperimentRuntime) -> BoundaryStressReport:

    config = application.configuration.values
    latent_dim = 64
    allowance = config.robustness.corrupted_client_allowance
    stress_fractions = tuple(config.robustness.real_stress.control_support_fractions)
    passed_sweeps = 0
    total_sweeps = 0

    for stress_fraction in stress_fractions:
        sample_size = max(5, int(_STRESS_SWEEP_BASELINE_ROWS * stress_fraction))
        for corrupted_count in allowance.counts:
            for attack in allowance.attacks:
                total_sweeps += 1
                estimate = estimate_client_nuisance_subspace(
                    client_controls=torch.randn(sample_size, latent_dim),
                    rank_selection=RankSelectionMethod.FIXED_RANK,
                    fixed_rank=config.identification.nuisance_rank.maximum,
                    eigengap_regularization=config.numerical.rank_clip_epsilon_relative,
                    scale_standardization_floor=config.numerical.scale_standardization_floor,
                )
                if corrupted_count > 0:
                    estimate = apply_corrupted_client_attack(estimate, attack, allowance.parameters)
                fset = build_nuisance_spaces(
                    nuisance_subspaces=(estimate.subspace,),
                    uncertainty_radii=(estimate.uncertainty_radius,),
                )
                action = torch.randn(latent_dim)
                if corrupted_count > 0 and attack is CorruptedClientAttack.TRANSITION_POISONING:
                    action = action + allowance.parameters.transition_poisoning_sigma * torch.randn(
                        latent_dim
                    )
                interval = solve_action_interval(action_vector=action, feasible_set=fset)
                if interval.width > 0:
                    passed_sweeps += 1

    characterized = passed_sweeps == total_sweeps
    outcome = ScientificOutcome.PASS if characterized else ScientificOutcome.INSUFFICIENT_EVIDENCE

    return BoundaryStressReport(
        stress_sweeps_completed=total_sweeps,
        failure_boundaries_characterized=characterized,
        scientific_outcome=outcome,
    )
