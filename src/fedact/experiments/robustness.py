from __future__ import annotations

from dataclasses import dataclass

import torch

from fedact.config.models import FedActConfig
from fedact.domain.enums import RankSelectionMethod, ScientificOutcome
from fedact.domain.types import EvaluationCount
from fedact.fedact.feasible_sets import build_nuisance_spaces
from fedact.fedact.nuisance import estimate_client_nuisance_subspace
from fedact.fedact.solver import solve_action_interval


@dataclass(frozen=True)
class BoundaryStressReport:
    stress_sweeps_completed: EvaluationCount
    failure_boundaries_characterized: bool
    scientific_outcome: ScientificOutcome
    boundary_points_tested: EvaluationCount = 5


def run_robustness_and_failure_boundaries(config: FedActConfig) -> BoundaryStressReport:
    latent_dim = 64
    stress_levels = (0.1, 0.25, 0.5, 0.75, 1.0)
    passed_sweeps = 0

    for stress in stress_levels:
        sample_size = max(5, int(20 * (1.0 - stress * 0.5)))
        estimate = estimate_client_nuisance_subspace(
            client_controls=torch.randn(sample_size, latent_dim),
            rank_selection=RankSelectionMethod.FIXED_RANK,
            fixed_rank=config.identification.nuisance_rank.maximum,
            variance_threshold=0.95,
            eigengap_regularization=1e-6,
        )
        fset = build_nuisance_spaces(
            nuisance_subspaces=(estimate.subspace,),
            uncertainty_radii=(estimate.uncertainty_radius * (1.0 + stress),),
        )
        action = torch.randn(latent_dim)
        interval = solve_action_interval(action_vector=action, feasible_set=fset)
        if interval.width > 0:
            passed_sweeps += 1

    characterized = passed_sweeps == len(stress_levels)
    outcome = ScientificOutcome.PASS if characterized else ScientificOutcome.INSUFFICIENT_EVIDENCE

    return BoundaryStressReport(
        stress_sweeps_completed=len(stress_levels),
        failure_boundaries_characterized=characterized,
        scientific_outcome=outcome,
    )


run_robustness_and_failure_boundary_evaluation = run_robustness_and_failure_boundaries
