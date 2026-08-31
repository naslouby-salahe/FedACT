from __future__ import annotations

import torch

from fedact.app import Application
from fedact.config.models import CorruptedClientAllowanceParameters, CorruptedClientAttack
from fedact.core.nuisance import NuisanceEstimate
from fedact.domain.enums import ScientificOutcome
from fedact.experiments.failure_boundaries import (
    apply_corrupted_client_attack,
    run_robustness_and_failure_boundaries,
)


def test_run_robustness_and_failure_boundary_evaluation(
    application: Application,
) -> None:
    report = run_robustness_and_failure_boundaries(application)
    assert report.boundary_points_tested > 0
    assert report.scientific_outcome is ScientificOutcome.PASS


def _base_estimate() -> NuisanceEstimate:
    return NuisanceEstimate(
        subspace=torch.eye(4)[:, :2],
        uncertainty_radius=0.1,
        selected_rank=2,
        eigengap_ratio=1.5,
        replicates=(),
    )


def _parameters() -> CorruptedClientAllowanceParameters:
    return CorruptedClientAllowanceParameters(
        basis_rotation_degrees=90.0,
        false_rank_increment=2,
        beta_multiplier=0.5,
        transition_poisoning_sigma=2.0,
        fabricated_complementarity_rotation_degrees=45.0,
    )


def test_basis_rotation_attack_rotates_the_subspace() -> None:
    estimate = _base_estimate()
    corrupted = apply_corrupted_client_attack(
        estimate, CorruptedClientAttack.BASIS_ROTATION, _parameters()
    )
    assert not torch.allclose(corrupted.subspace, estimate.subspace)


def test_false_rank_reporting_increments_selected_rank() -> None:
    estimate = _base_estimate()
    corrupted = apply_corrupted_client_attack(
        estimate, CorruptedClientAttack.FALSE_RANK_REPORTING, _parameters()
    )
    assert corrupted.selected_rank == estimate.selected_rank + 2


def test_beta_under_reporting_scales_uncertainty_radius() -> None:
    estimate = _base_estimate()
    corrupted = apply_corrupted_client_attack(
        estimate, CorruptedClientAttack.BETA_UNDER_REPORTING, _parameters()
    )
    assert corrupted.uncertainty_radius == estimate.uncertainty_radius * 0.5
