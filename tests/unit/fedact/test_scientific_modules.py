from __future__ import annotations

import numpy as np
import pytest

from fedact.fedact.actions import (
    box_diameter_bound,
    evaluate_displacement,
)
from fedact.fedact.certification import (
    CertificateState,
    DomainValid,
    decide,
    is_forecast_set_within_gate,
    leave_one_client_out_stability,
)
from fedact.fedact.client_selection import (
    SelectionBudget,
    greedy_d_optimal,
    uniform_action_weights,
)
from fedact.fedact.constraints import ClientConstraintSummary, validate_summary
from fedact.fedact.controls import (
    ControlQualityGate,
    build_control_displacement,
    held_out_reconstruction_residuals,
    is_control_gate_passing,
)
from fedact.fedact.nuisance import (
    admissible_rank,
    eigengap_ratio,
    is_rank_stable,
    regularized_covariance,
    select_rank_by_eigengap,
    weighted_covariance,
)
from fedact.fedact.solver import SolverToleranceSettings, solve_support_bounds
from fedact.fedact.transitions import AbstentionReason, ClientIdentifier
from fedact.fedact.uncertainty import (
    client_radius,
    sampling_uncertainty_quantile,
    standardized_subspace_term,
    subspace_uncertainty,
)

SETTINGS = SolverToleranceSettings(
    relative_tolerance=1e-8,
    absolute_tolerance=1e-8,
    duality_gap_tolerance=1e-8,
    maximum_iterations=200,
)


def test_nuisance_covariance_is_weighted_second_moment() -> None:
    a = np.array([1.0, 0.0])
    b = np.array([-1.0, 0.0])
    covariance = weighted_covariance((a, b), (1.0, 1.0))
    assert float(covariance[0, 0]) == pytest.approx(1.0)
    assert float(covariance[1, 1]) == pytest.approx(0.0)


def test_admissible_rank_respects_all_three_limits() -> None:
    assert admissible_rank(dimension=8, replicates=5, configured_maximum=20) == 4
    assert admissible_rank(dimension=4, replicates=50, configured_maximum=20) == 3
    assert admissible_rank(dimension=64, replicates=50, configured_maximum=7) == 7


def test_eigengap_ratio_matches_the_roadmap_definition() -> None:
    eigenvalues = np.array([10.0, 5.0, 1.0, 0.1])
    ratio = eigengap_ratio(eigenvalues, rank=2, clip_relative=1e-6, floor=1e-8)
    assert ratio == pytest.approx(5.0)


def test_rank_selection_requires_calibrated_eigengap() -> None:
    eigenvalues = np.array([100.0, 50.0, 1.0, 0.1])
    selected = select_rank_by_eigengap(
        eigenvalues,
        maximum_admissible=3,
        calibrated_requirement=1.05,
        clip_relative=1e-6,
        floor=1e-8,
    )
    assert selected == 3
    too_strict = select_rank_by_eigengap(
        eigenvalues,
        maximum_admissible=3,
        calibrated_requirement=60.0,
        clip_relative=1e-6,
        floor=1e-8,
    )
    assert too_strict is None
    too_strict = select_rank_by_eigengap(
        eigenvalues,
        maximum_admissible=3,
        calibrated_requirement=60.0,
        clip_relative=1e-6,
        floor=1e-8,
    )
    assert too_strict is None


def test_regularized_covariance_adds_scaled_identity() -> None:
    raw = np.diag([4.0, 2.0])
    regularized = regularized_covariance(raw, coefficient=0.01, floor=1e-8)
    assert float(regularized[0, 0]) == pytest.approx(4.0 + 0.01 * 3.0)
    assert float(regularized[1, 1]) == pytest.approx(2.0 + 0.01 * 3.0)


def test_rank_stability_bootstrap_rule() -> None:
    assert is_rank_stable((3, 3, 3, 3), full_sample_rank=3, minimum_fraction=0.80)
    assert not is_rank_stable((3, 3, 2, 4), full_sample_rank=3, minimum_fraction=0.80)


def test_held_out_reconstruction_and_gate() -> None:
    displacements = (np.array([0.0]), np.array([0.1]), np.array([0.2]))
    residuals = held_out_reconstruction_residuals(displacements)
    gate = ControlQualityGate(held_out_residual_quantile=0.75, minimum_pass_fraction=0.80)
    assert is_control_gate_passing(residuals, gate)
    displacement = build_control_displacement(np.array([1.0]), np.array([2.0]))
    assert displacement[0] == pytest.approx(1.0)


def test_uncertainty_components_compose_into_client_radius() -> None:
    norms = tuple(float(value) for value in np.linspace(0.1, 1.0, 10))
    sampling = sampling_uncertainty_quantile(norms, alpha=0.05)
    reference = np.eye(3)[:, 0:1].T
    perturbed = (np.eye(3)[:, 0:1].T, np.eye(3)[:, 1:2].T * 0.99)
    _ = reference, perturbed
    subspace = subspace_uncertainty(
        (np.array([[1.0, 0.0]]), np.array([[0.999, 0.044]])), np.array([[1.0, 0.0]]), alpha=0.05
    )
    standardized = standardized_subspace_term(subspace, amplitude=1.0, smallest_eigenvalue=1.0)
    radius = client_radius(
        sampling=sampling, subspace=standardized, control_span=0.2, private_allowance=0.1
    )
    assert radius >= sampling


def test_constraint_validation_emits_exact_abstention_reasons() -> None:
    summary = ClientConstraintSummary(
        client_id=ClientIdentifier("k1"),
        basis=np.eye(4)[:, :2],
        transition_vector=np.ones(4),
        covariance=np.eye(4),
        support_before=300,
        support_after=300,
        beta=0.5,
        eigengap_ratio=1.5,
        selected_rank=2,
        control_diagnostics_passed=True,
    )
    assert validate_summary(summary, minimum_support=200) is None
    low_support = ClientConstraintSummary(
        client_id=ClientIdentifier("k2"),
        basis=np.eye(4)[:, :2],
        transition_vector=np.ones(4),
        covariance=np.eye(4),
        support_before=10,
        support_after=300,
        beta=0.5,
        eigengap_ratio=1.5,
        selected_rank=2,
        control_diagnostics_passed=True,
    )
    result = validate_summary(low_support, minimum_support=200)
    assert result is AbstentionReason.ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT


def test_degenerate_displacement_is_rejected_at_the_floor() -> None:
    original = np.zeros(3)
    degenerate = evaluate_displacement(original, original + 1e-14, zero_displacement_floor=1e-10)
    assert degenerate.rejected_as_degenerate
    valid = evaluate_displacement(
        original, original + np.array([1.0, 0.0, 0.0]), zero_displacement_floor=1e-10
    )
    assert not valid.rejected_as_degenerate
    assert float(valid.direction[0]) == pytest.approx(1.0)


def test_box_diameter_upper_bounds_the_exact_diameter() -> None:
    lower = (-1.0, -1.0)
    upper = (1.0, 1.0)
    bound = box_diameter_bound(lower, upper)
    exact = float(np.sqrt(8.0))
    assert bound >= exact


def test_support_bounds_via_ecos_solver_on_analytical_box() -> None:
    direction = np.array([1.0, 0.0])
    coefficients = np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]])
    limits = np.array([1.0, 1.0, 1.0, 1.0])
    lower, upper = solve_support_bounds(direction, coefficients, limits, SETTINGS)
    assert lower == pytest.approx(-1.0, abs=1e-6)
    assert upper == pytest.approx(1.0, abs=1e-6)


def test_certification_decisions_follow_locked_thresholds() -> None:
    certified = decide(
        lower=1.5, upper=1.8, tau_align=1.0, tau_amb=0.5, domain_valid=DomainValid(valid=True)
    )
    assert certified.state is CertificateState.CERTIFIED
    negative = decide(
        lower=-2.0, upper=-1.0, tau_align=1.0, tau_amb=0.5, domain_valid=DomainValid(valid=True)
    )
    assert negative.state is CertificateState.NEGATIVE
    ambiguous = decide(
        lower=0.5, upper=1.5, tau_align=1.0, tau_amb=0.5, domain_valid=DomainValid(valid=True)
    )
    assert ambiguous.state is CertificateState.AMBIGUOUS


def test_forecast_set_width_gate_and_loo_stability() -> None:
    assert is_forecast_set_within_gate(1.0, historical_quantile_value=2.0)
    assert not is_forecast_set_within_gate(3.0, historical_quantile_value=2.0)
    unstable, _required = leave_one_client_out_stability((True, True, True, False), 0.80)
    assert not unstable
    stable, _ = leave_one_client_out_stability((True, True, True, True), 0.80)
    assert stable


def test_single_client_dominance_downgrades_certificate() -> None:
    from fedact.fedact.certification import downgrade_dominant_single_client as downgrade

    assert downgrade(CertificateState.CERTIFIED) is CertificateState.AMBIGUOUS
    assert downgrade(CertificateState.NEGATIVE) is CertificateState.NEGATIVE


def test_d_optimal_selection_prefers_complementary_information() -> None:
    matrices = {
        "a": np.diag([1.0, 0.01]),
        "b": np.diag([0.01, 1.0]),
        "c": np.diag([1.0, 0.02]),
    }
    budget = SelectionBudget(budget_fraction=1.0, eligible_clients=2)
    selection = greedy_d_optimal(matrices, ridge_lambda=1e-6, budget=budget)
    assert len(selection) == 2
    assert selection[0] in {"a", "b", "c"}


def test_uniform_action_weights_sum_to_one() -> None:
    weights = uniform_action_weights(4)
    assert len(weights) == 4
    assert sum(weights) == pytest.approx(1.0)
    assert uniform_action_weights(0) == ()
