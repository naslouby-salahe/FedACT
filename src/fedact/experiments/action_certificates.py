from __future__ import annotations

from dataclasses import dataclass

import torch

from fedact.config.models import FedActConfig
from fedact.domain.enums import CertificationStatus, RankSelectionMethod, ScientificOutcome
from fedact.domain.types import EvaluationCount, MetricRate
from fedact.fedact.certification import DomainValid, certify_action_interval
from fedact.fedact.feasible_sets import build_nuisance_spaces
from fedact.fedact.nuisance import estimate_client_nuisance_subspace
from fedact.fedact.solver import solve_action_interval


@dataclass(frozen=True)
class ActionCertificateReport:
    total_actions: EvaluationCount
    certified_positive_count: EvaluationCount
    ambiguous_count: EvaluationCount
    abstention_count: EvaluationCount
    coverage_rate: MetricRate
    scientific_outcome: ScientificOutcome


def run_action_certificate_validation(config: FedActConfig) -> ActionCertificateReport:
    latent_dim = 64
    nuisance_estimates = [
        estimate_client_nuisance_subspace(
            client_controls=torch.randn(20, latent_dim),
            rank_selection=RankSelectionMethod.FIXED_RANK,
            fixed_rank=config.identification.nuisance_rank.maximum,
            variance_threshold=0.95,
            eigengap_regularization=config.numerical.rank_clip_epsilon_relative,
            scale_standardization_floor=config.numerical.scale_standardization_floor,
        )
        for _unused in range(5)
    ]
    feasible_set = build_nuisance_spaces(
        nuisance_subspaces=tuple(e.subspace for e in nuisance_estimates),
        uncertainty_radii=tuple(0.01 for _unused in nuisance_estimates),
    )
    actions = [torch.ones(latent_dim) * 2.0 for _unused in range(50)]

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
            historical_realized_diameter_quantile=2.0,
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
