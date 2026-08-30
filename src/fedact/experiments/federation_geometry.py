from __future__ import annotations

from dataclasses import dataclass

import torch

from fedact.config.models import FedActConfig
from fedact.domain.enums import FederationGeometry, RankSelectionMethod, ScientificOutcome
from fedact.domain.types import EvaluationCount, IntervalBound
from fedact.fedact.feasible_sets import build_nuisance_spaces
from fedact.fedact.nuisance import estimate_client_nuisance_subspace
from fedact.fedact.solver import solve_action_interval


@dataclass(frozen=True)
class FederationGeometryReport:
    clients_evaluated: EvaluationCount
    delta_w_o: IntervalBound
    complementarity_verified: bool
    scientific_outcome: ScientificOutcome
    geometries_tested: EvaluationCount = 2


def run_federation_geometry_evaluation(config: FedActConfig) -> FederationGeometryReport:
    latent_dim = 64
    k = 5

    estimates = [
        estimate_client_nuisance_subspace(
            client_controls=torch.randn(20, latent_dim),
            rank_selection=RankSelectionMethod.FIXED_RANK,
            fixed_rank=config.identification.nuisance_rank.maximum,
            variance_threshold=0.95,
            eigengap_regularization=config.numerical.rank_clip_epsilon_relative,
            scale_standardization_floor=config.numerical.scale_standardization_floor,
        )
        for _unused in range(k)
    ]

    comp_set = build_nuisance_spaces(
        nuisance_subspaces=tuple(e.subspace for e in estimates),
        uncertainty_radii=tuple(e.uncertainty_radius for e in estimates),
        geometry=FederationGeometry.COMPLEMENTARY,
    )
    red_set = build_nuisance_spaces(
        nuisance_subspaces=tuple(e.subspace for e in estimates),
        uncertainty_radii=tuple(e.uncertainty_radius for e in estimates),
        geometry=FederationGeometry.REDUNDANT,
    )

    action = torch.randn(latent_dim)
    w_comp = solve_action_interval(action_vector=action, feasible_set=comp_set).width
    w_red = solve_action_interval(action_vector=action, feasible_set=red_set).width

    delta_w = float(w_red - w_comp)
    verified = bool(delta_w >= -1e-6)
    outcome = ScientificOutcome.PASS if verified else ScientificOutcome.FAIL

    return FederationGeometryReport(
        clients_evaluated=k,
        delta_w_o=delta_w,
        complementarity_verified=verified,
        scientific_outcome=outcome,
    )


run_federation_and_complementarity_evaluation = run_federation_geometry_evaluation
