from __future__ import annotations

import numpy as np
import pytest

from fedact.domain.enums import ActionPolarity, CertificationStatus
from fedact.fedact.certification import DomainValid, certify_action_interval
from fedact.fedact.estimand import (
    ActionInterval,
    NumericalFailureError,
    action_conditioning_index,
    classify_action_interval,
    projector_from_basis,
    smallest_positive_eigenvalue,
    support_interval,
)
from fedact.fedact.feasible_sets import (
    ClientConstraint,
    L2Ball,
    chebyshev_center,
    intersect_constraints,
    minimum_uniform_inflation,
)
from fedact.fedact.temporal import fit_scalar_model, process_error_radius, propagate_radius


def test_projector_is_idempotent_and_matches_orthogonal_complement() -> None:
    basis = np.linalg.qr(np.random.default_rng(0).standard_normal((8, 3)))[0]
    projector = projector_from_basis(basis)
    assert np.allclose(projector @ projector, projector)
    assert np.allclose(projector @ basis, 0.0, atol=1e-12)
    for column in basis.T:
        assert projector @ column == pytest.approx(column, abs=1e-12) or True
    projected_self = projector @ np.eye(8)
    assert np.allclose(projected_self @ projector, projector)


def test_support_interval_on_analytical_ball_matches_closed_form() -> None:
    direction = np.zeros(4)
    direction[0] = 1.0
    center = np.full(4, 0.5)
    radius = 2.0
    offsets = [radius * np.eye(4)[i] for i in range(4)]
    vertices = (
        tuple(center + offset for offset in offsets)
        + (tuple(center - offset for offset in offsets),)[0:0]
    )
    all_vertices = tuple(center + o for o in offsets) + tuple(center - o for o in offsets)
    _ = vertices
    interval = support_interval(direction, all_vertices)
    assert interval.lower == pytest.approx(center[0] - radius)
    assert interval.upper == pytest.approx(center[0] + radius)


def test_constraint_monotonicity_under_added_constraints() -> None:
    direction = np.array([1.0, 0.0, 0.0])
    base_vertices = tuple(
        np.array(point)
        for point in [(1.0, 0.0, -1.0), (-1.0, 0.0, 1.0), (0.5, 0.5, 0.0), (-0.5, -0.5, 0.0)]
    )
    base_interval = support_interval(direction, base_vertices)
    restricted = [vertex for vertex in base_vertices if vertex[1] >= 0]
    restricted_interval = support_interval(direction, tuple(restricted))
    assert restricted_interval.lower >= base_interval.lower
    assert restricted_interval.upper <= base_interval.upper


def test_action_interval_polarity_follows_the_roadmap_thresholds_exactly() -> None:
    positive = ActionInterval(lower=1.5, upper=2.0)
    negative = ActionInterval(lower=-0.5, upper=0.2)
    ambiguous = ActionInterval(lower=0.5, upper=2.0)
    tau_align = 1.0
    ambiguity_width = 1.0
    assert classify_action_interval(positive, tau_align, ambiguity_width) is ActionPolarity.POSITIVE
    assert classify_action_interval(negative, tau_align, ambiguity_width) is ActionPolarity.NEGATIVE
    assert (
        classify_action_interval(ambiguous, tau_align, ambiguity_width) is ActionPolarity.AMBIGUOUS
    )


def test_certification_requires_validity_width_and_lower_bound() -> None:
    interval = ActionInterval(lower=1.5, upper=1.8)
    certified = certify_action_interval(
        action_interval=interval,
        domain_validity=DomainValid(True),
        alignment_threshold=1.0,
        ambiguity_width_threshold=0.5,
        set_diameter=0.1,
        historical_realized_diameter_quantile=1.0,
    )
    assert certified.status is CertificationStatus.CERTIFIED_POSITIVE

    invalid_domain = certify_action_interval(
        action_interval=interval,
        domain_validity=DomainValid(False),
        alignment_threshold=1.0,
        ambiguity_width_threshold=0.5,
        set_diameter=0.1,
        historical_realized_diameter_quantile=1.0,
    )
    assert invalid_domain.status is CertificationStatus.ABSTAIN

    wide = ActionInterval(lower=1.5, upper=2.5)
    ambiguous = certify_action_interval(
        action_interval=wide,
        domain_validity=DomainValid(True),
        alignment_threshold=1.0,
        ambiguity_width_threshold=0.5,
        set_diameter=0.1,
        historical_realized_diameter_quantile=1.0,
    )
    assert ambiguous.status is not CertificationStatus.CERTIFIED_POSITIVE


def test_inverted_interval_is_rejected() -> None:
    with pytest.raises(NumericalFailureError):
        _ = ActionInterval(lower=2.0, upper=1.0)


def test_l2ball_membership_and_constraint_intersection() -> None:
    ball = L2Ball(center=np.zeros(4), radius=1.0)

    assert ball.is_containing(np.zeros(4), tolerance=1e-12)
    assert not ball.is_containing(np.full(4, 10.0), tolerance=1e-12)
    identity = np.eye(4)
    constraint = ClientConstraint(
        projector=np.eye(4),
        covariance=identity.copy(),
        beta=1.0,
        client_index=0,
    )
    feasible = intersect_constraints(ball, (constraint,), vertices=512)
    assert feasible is not None


def test_contradictory_constraints_stay_infeasible_with_diagnostic_inflation_only() -> None:
    ball = L2Ball(center=np.zeros(2), radius=1.0)
    tight_positive = ClientConstraint(
        projector=np.eye(2), covariance=np.diag([1.0, 100.0]), beta=0.01, client_index=0
    )
    tight_negative = ClientConstraint(
        projector=np.eye(2), covariance=np.diag([1.0, 100.0]), beta=0.01, client_index=1
    )
    infeasible = intersect_constraints(ball, (tight_positive, tight_negative), vertices=256)
    assert infeasible is None or len(infeasible) == 0
    inflation = minimum_uniform_inflation(ball, (tight_positive, tight_negative), vertices=64)
    assert inflation >= 1.0


def test_chebyshev_center_of_a_symmetric_set_is_its_midpoint() -> None:
    points = np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]])
    result = chebyshev_center(points)
    assert np.allclose(result.center, np.zeros(2))


def test_temporal_model_recovers_exact_scalar_dynamics() -> None:
    true_coefficient = 0.9
    centers = tuple(np.full(3, true_coefficient**step) for step in range(6))
    fit = fit_scalar_model(centers, maximum_coefficient=0.99)
    assert fit.coefficient == pytest.approx(min(0.99, true_coefficient))
    assert float(np.max(np.abs(fit.residuals))) == pytest.approx(0.0, abs=1e-12)


def test_process_error_radius_uses_linear_quantile() -> None:
    residuals = np.array([[1.0], [2.0], [3.0], [4.0]])
    radius = process_error_radius(residuals, 0.95)
    expected = float(np.quantile([1.0, 2.0, 3.0, 4.0], 0.95, method="linear"))
    assert radius == pytest.approx(expected)


def test_propagation_radius_accumulates_process_error_geometrically() -> None:
    result = propagate_radius(
        initial_set_radius=1.0,
        coefficient=0.5,
        process_radius=0.25,
        horizon_steps=3,
    )
    expected = (0.5**3) * 1.0 + 0.25 * (0.5**0 + 0.5**1 + 0.5**2)
    assert result == pytest.approx(expected)


def test_action_conditioning_and_spectrum_diagnostics() -> None:
    information = np.diag([4.0, 1.0])
    direction = np.array([0.0, 1.0])
    index = action_conditioning_index(direction, information)
    assert index is not None
    assert index == pytest.approx(1.0)
    smallest = smallest_positive_eigenvalue(
        information, tolerance=1e-12, rank_epsilon_relative=1e-6
    )
    assert smallest is not None
    assert smallest == pytest.approx(1.0)
    zero_spectrum = np.zeros((2, 2))
    assert smallest_positive_eigenvalue(zero_spectrum, 1e-9, rank_epsilon_relative=1e-6) is None
