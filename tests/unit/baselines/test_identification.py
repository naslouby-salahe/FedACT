from __future__ import annotations

import numpy as np
import pytest

from fedact.domain.types import ClientIdentifier
from fedact.experiments.baselines import (
    ClientPointCandidate,
    average_projected_residual,
    best_individual_client,
    covariance_weighted_reconstruction,
    matched_benign_subtraction,
    nuisance_projection_without_intersection,
    point_estimate_with_matched_isotropic_uncertainty,
    projected_point_reconstruction,
    pseudoinverse_point_reconstruction,
    raw_malicious_transition_forecast,
    regularized_point_reconstruction,
    robust_raw_aggregation,
)


def test_matched_benign_subtraction() -> None:
    mal = np.array([2.0, 3.0])
    ben = np.array([1.0, 1.0])
    res = matched_benign_subtraction(mal, ben)
    assert np.allclose(res.estimated_displacement, np.array([1.0, 2.0]))


def test_projected_point_reconstruction() -> None:
    mal = np.array([1.0, 2.0])
    basis = np.array([[1.0], [0.0]])
    res = projected_point_reconstruction(mal, basis)
    assert np.allclose(res.estimated_displacement, np.array([0.0, 2.0]))


def test_covariance_weighted_reconstruction() -> None:
    mal = np.array([1.0, 2.0])
    cov = np.eye(2)
    res = covariance_weighted_reconstruction(mal, cov, ridge=1e-4)
    assert res.estimated_displacement.shape == (2,)


def test_raw_malicious_transition_forecast_weights_by_effective_support() -> None:
    transitions = [np.array([1.0, 0.0]), np.array([3.0, 0.0])]
    supports = [(10, 10), (10, 10)]
    res = raw_malicious_transition_forecast(transitions, supports)
    assert np.allclose(res.estimated_displacement, np.array([2.0, 0.0]))


def test_raw_malicious_transition_forecast_rejects_zero_support() -> None:
    with pytest.raises(ValueError, match="effective support"):
        raw_malicious_transition_forecast([np.array([1.0])], [(0, 0)])


def test_average_projected_residual_matches_weighted_mean() -> None:
    projected = [np.array([2.0, 2.0]), np.array([4.0, 4.0])]
    supports = [(5, 5), (15, 15)]
    res = average_projected_residual(projected, supports)
    expected = (2.5 * np.array([2.0, 2.0]) + 7.5 * np.array([4.0, 4.0])) / 10.0
    assert np.allclose(res.estimated_displacement, expected)


def test_pseudoinverse_point_reconstruction_recovers_exact_solution() -> None:
    matrix = np.eye(2)
    target = np.array([3.0, -1.0])
    res = pseudoinverse_point_reconstruction(matrix, target, rank_clip_epsilon_relative=1e-10)
    assert np.allclose(res.estimated_displacement, target)


def test_regularized_point_reconstruction_shrinks_toward_zero() -> None:
    matrix = np.eye(2)
    target = np.array([1.0, 1.0])
    unregularized = regularized_point_reconstruction(matrix, target, 0.0, 1e-12)
    regularized = regularized_point_reconstruction(matrix, target, 10.0, 1e-12)
    assert np.linalg.norm(regularized.estimated_displacement) < np.linalg.norm(
        unregularized.estimated_displacement
    )


def test_robust_raw_aggregation_matches_geometric_median_of_transitions() -> None:
    transitions = [np.array([0.0, 0.0]), np.array([1.0, 0.0]), np.array([100.0, 0.0])]
    res = robust_raw_aggregation(transitions, 1e-8, 200)
    assert np.allclose(res.estimated_displacement, np.array([1.0, 0.0]), atol=1e-3)


def test_nuisance_projection_without_intersection_matches_geometric_median() -> None:
    projected = [np.array([0.0, 1.0]), np.array([0.0, 1.0]), np.array([0.0, 50.0])]
    res = nuisance_projection_without_intersection(projected, 1e-8, 200)
    assert np.allclose(res.estimated_displacement, np.array([0.0, 1.0]), atol=1e-3)


def test_best_individual_client_selects_smallest_beta() -> None:
    candidates = [
        ClientPointCandidate(
            client_id=ClientIdentifier("client-a"),
            beta=0.5,
            malicious_effective_support=10.0,
            stacked_system_matrix=np.eye(2),
            stacked_system_target=np.array([1.0, 1.0]),
        ),
        ClientPointCandidate(
            client_id=ClientIdentifier("client-b"),
            beta=0.1,
            malicious_effective_support=5.0,
            stacked_system_matrix=np.eye(2),
            stacked_system_target=np.array([9.0, 9.0]),
        ),
    ]
    res = best_individual_client(candidates, rank_clip_epsilon_relative=1e-10)
    assert np.allclose(res.estimated_displacement, np.array([9.0, 9.0]))


def test_best_individual_client_breaks_beta_ties_by_larger_support_then_lexical_id() -> None:
    candidates = [
        ClientPointCandidate(
            client_id=ClientIdentifier("z-client"),
            beta=0.2,
            malicious_effective_support=20.0,
            stacked_system_matrix=np.eye(2),
            stacked_system_target=np.array([1.0, 0.0]),
        ),
        ClientPointCandidate(
            client_id=ClientIdentifier("a-client"),
            beta=0.2,
            malicious_effective_support=20.0,
            stacked_system_matrix=np.eye(2),
            stacked_system_target=np.array([2.0, 0.0]),
        ),
    ]
    res = best_individual_client(candidates, rank_clip_epsilon_relative=1e-10)
    assert np.allclose(res.estimated_displacement, np.array([2.0, 0.0]))


def test_point_estimate_with_matched_isotropic_uncertainty_centers_ball_on_point() -> None:
    point = np.array([1.0, -2.0])
    ball = point_estimate_with_matched_isotropic_uncertainty(point, matched_radius=0.5)
    assert np.allclose(ball.center, point)
    assert ball.radius == 0.5
    assert ball.is_containing(np.array([1.0, -1.6]), tolerance=0.0)
    assert not ball.is_containing(np.array([1.0, -1.0]), tolerance=0.0)
