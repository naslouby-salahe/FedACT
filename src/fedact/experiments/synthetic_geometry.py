from __future__ import annotations

from dataclasses import dataclass

import torch

from fedact.config.models import CorruptedClientAttack, FedActConfig, SyntheticCorruptionAttack
from fedact.domain.enums import CertificationStatus, RankSelectionMethod, ScientificOutcome
from fedact.domain.types import (
    IntervalBound,
    MetricRate,
    ParameterName,
    ParameterValue,
    SampleCount,
)
from fedact.experiments.robustness import apply_corrupted_client_attack
from fedact.fedact.certification import DomainValid, certify_action_interval
from fedact.fedact.feasible_sets import build_nuisance_spaces
from fedact.fedact.nuisance import estimate_client_nuisance_subspace
from fedact.fedact.solver import solve_action_interval

_SYNTHETIC_TO_CORRUPTED_CLIENT_ATTACK = {
    SyntheticCorruptionAttack.ROTATION: CorruptedClientAttack.BASIS_ROTATION,
    SyntheticCorruptionAttack.RANK_MISREPORT: CorruptedClientAttack.FALSE_RANK_REPORTING,
    SyntheticCorruptionAttack.BETA_UNDERREPORT: CorruptedClientAttack.BETA_UNDER_REPORTING,
    SyntheticCorruptionAttack.POISONING: CorruptedClientAttack.TRANSITION_POISONING,
    SyntheticCorruptionAttack.FABRICATED_COMPLEMENTARITY: (
        CorruptedClientAttack.FABRICATED_COMPLEMENTARITY
    ),
}


@dataclass(frozen=True)
class SweepCellResult:
    parameter_name: ParameterName
    parameter_value: ParameterValue
    coverage: MetricRate
    action_width: IntervalBound
    is_certified: bool
    is_ambiguous: bool
    is_abstaining: bool


@dataclass(frozen=True)
class SyntheticSweepReport:
    total_cells: SampleCount
    passed_cells: SampleCount
    mechanism_valid: bool
    cells: tuple[SweepCellResult, ...]
    scientific_outcome: ScientificOutcome


def run_synthetic_geometry_sweeps(config: FedActConfig) -> SyntheticSweepReport:
    latent_dim = 64
    sigmas = config.synthetic.sweeps.synchronized_nuisance_over_sigma
    cells: list[SweepCellResult] = []

    for sigma in sigmas:
        estimate = estimate_client_nuisance_subspace(
            client_controls=torch.randn(20, latent_dim) * float(sigma),
            rank_selection=RankSelectionMethod.FIXED_RANK,
            fixed_rank=config.identification.nuisance_rank.maximum,
            variance_threshold=0.95,
            eigengap_regularization=config.numerical.rank_clip_epsilon_relative,
            scale_standardization_floor=config.numerical.scale_standardization_floor,
        )
        fset = build_nuisance_spaces(
            nuisance_subspaces=(estimate.subspace,),
            uncertainty_radii=(estimate.uncertainty_radius,),
        )
        action = torch.randn(latent_dim)
        interval = solve_action_interval(action_vector=action, feasible_set=fset)
        decision = certify_action_interval(
            action_interval=interval,
            domain_validity=DomainValid(valid=True),
            alignment_threshold=config.certification.alignment_threshold.percentile_candidates[0]
            / 100.0,
            ambiguity_width_threshold=config.certification.ambiguity_width.percentile_candidates[-1]
            / 100.0,
            set_diameter=fset.diameter,
            historical_realized_diameter_quantile=config.certification.forecast_set_diameter_abstention.historical_realized_diameter_quantile,
        )
        cells.append(
            SweepCellResult(
                parameter_name="nuisance_variance",
                parameter_value=float(sigma),
                coverage=1.0 if decision.status is CertificationStatus.CERTIFIED_POSITIVE else 0.0,
                action_width=interval.width,
                is_certified=decision.status is CertificationStatus.CERTIFIED_POSITIVE,
                is_ambiguous=decision.status is CertificationStatus.AMBIGUOUS,
                is_abstaining=decision.status is CertificationStatus.ABSTAIN,
            )
        )

    outlier_sweep = config.synthetic.sweeps.outlier_client_stress
    for corrupted_count in outlier_sweep.corrupted_client_counts:
        for synthetic_attack in outlier_sweep.attacks:
            estimate = estimate_client_nuisance_subspace(
                client_controls=torch.randn(20, latent_dim),
                rank_selection=RankSelectionMethod.FIXED_RANK,
                fixed_rank=config.identification.nuisance_rank.maximum,
                variance_threshold=0.95,
                eigengap_regularization=config.numerical.rank_clip_epsilon_relative,
                scale_standardization_floor=config.numerical.scale_standardization_floor,
            )
            action = torch.randn(latent_dim)
            if corrupted_count > 0:
                mapped_attack = _SYNTHETIC_TO_CORRUPTED_CLIENT_ATTACK[synthetic_attack]
                estimate = apply_corrupted_client_attack(
                    estimate, mapped_attack, config.robustness.corrupted_client_allowance.parameters
                )
                if mapped_attack is CorruptedClientAttack.TRANSITION_POISONING:
                    sigma_multiplier = config.robustness.corrupted_client_allowance.parameters.transition_poisoning_sigma
                    action = action + sigma_multiplier * torch.randn(latent_dim)
            fset = build_nuisance_spaces(
                nuisance_subspaces=(estimate.subspace,),
                uncertainty_radii=(estimate.uncertainty_radius,),
            )
            interval = solve_action_interval(action_vector=action, feasible_set=fset)
            decision = certify_action_interval(
                action_interval=interval,
                domain_validity=DomainValid(valid=True),
                alignment_threshold=config.certification.alignment_threshold.percentile_candidates[
                    0
                ]
                / 100.0,
                ambiguity_width_threshold=config.certification.ambiguity_width.percentile_candidates[
                    -1
                ]
                / 100.0,
                set_diameter=fset.diameter,
                historical_realized_diameter_quantile=config.certification.forecast_set_diameter_abstention.historical_realized_diameter_quantile,
            )
            cells.append(
                SweepCellResult(
                    parameter_name="outlier_client_stress",
                    parameter_value=float(corrupted_count),
                    coverage=(
                        1.0 if decision.status is CertificationStatus.CERTIFIED_POSITIVE else 0.0
                    ),
                    action_width=interval.width,
                    is_certified=decision.status is CertificationStatus.CERTIFIED_POSITIVE,
                    is_ambiguous=decision.status is CertificationStatus.AMBIGUOUS,
                    is_abstaining=decision.status is CertificationStatus.ABSTAIN,
                )
            )

    passed = sum(1 for c in cells if not c.is_abstaining)
    outcome = (
        ScientificOutcome.PASS
        if passed >= len(cells) * 0.5
        else ScientificOutcome.INSUFFICIENT_EVIDENCE
    )

    return SyntheticSweepReport(
        total_cells=len(cells),
        passed_cells=passed,
        mechanism_valid=passed > 0,
        cells=tuple(cells),
        scientific_outcome=outcome,
    )
