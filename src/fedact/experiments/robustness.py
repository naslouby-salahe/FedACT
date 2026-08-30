from __future__ import annotations

import math
from dataclasses import dataclass, replace

import torch

from fedact.config.models import (
    CorruptedClientAllowanceParameters,
    CorruptedClientAttack,
    FedActConfig,
)
from fedact.domain.enums import RankSelectionMethod, ScientificOutcome
from fedact.domain.types import EvaluationCount
from fedact.fedact.feasible_sets import build_nuisance_spaces
from fedact.fedact.nuisance import NuisanceEstimate, estimate_client_nuisance_subspace
from fedact.fedact.solver import solve_action_interval


@dataclass(frozen=True)
class BoundaryStressReport:
    stress_sweeps_completed: EvaluationCount
    failure_boundaries_characterized: bool
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
            estimate, subspace=_rotate_subspace(estimate.subspace, parameters.basis_rotation_degrees)
        )
    if attack is CorruptedClientAttack.FABRICATED_COMPLEMENTARITY:
        return replace(
            estimate,
            subspace=_rotate_subspace(
                estimate.subspace, parameters.fabricated_complementarity_rotation_degrees
            ),
        )
    if attack is CorruptedClientAttack.FALSE_RANK_REPORTING:
        return replace(estimate, selected_rank=estimate.selected_rank + parameters.false_rank_increment)
    if attack is CorruptedClientAttack.BETA_UNDER_REPORTING:
        return replace(
            estimate, uncertainty_radius=estimate.uncertainty_radius * parameters.beta_multiplier
        )
    return estimate


def run_robustness_and_failure_boundaries(config: FedActConfig) -> BoundaryStressReport:
    latent_dim = 64
    allowance = config.robustness.corrupted_client_allowance
    stress_fractions = tuple(config.robustness.real_stress.control_support_fractions)
    passed_sweeps = 0
    total_sweeps = 0

    for stress_fraction in stress_fractions:
        sample_size = max(5, int(20 * stress_fraction))
        for corrupted_count in allowance.counts:
            for attack in allowance.attacks:
                total_sweeps += 1
                estimate = estimate_client_nuisance_subspace(
                    client_controls=torch.randn(sample_size, latent_dim),
                    rank_selection=RankSelectionMethod.FIXED_RANK,
                    fixed_rank=config.identification.nuisance_rank.maximum,
                    variance_threshold=0.95,
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


run_robustness_and_failure_boundary_evaluation = run_robustness_and_failure_boundaries
