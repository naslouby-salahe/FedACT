from __future__ import annotations

import numpy as np
import pytest

from fedact.certification.client_procedure import (
    bootstrap_malicious_sampling_term,
    bootstrap_subspace_estimation_term,
    control_span_violation_term,
    mahalanobis_norm,
    malicious_transition_covariance,
    private_transition_term_single_client,
    select_stable_nuisance_rank,
)


def test_mahalanobis_norm_reduces_to_euclidean_norm_under_identity_covariance() -> None:
    vector = np.array([3.0, 4.0])
    assert mahalanobis_norm(vector, np.eye(2)) == pytest.approx(5.0)


def test_mahalanobis_norm_scales_inversely_with_variance() -> None:
    vector = np.array([2.0, 0.0])
    covariance = np.diag([4.0, 1.0])
    assert mahalanobis_norm(vector, covariance) == pytest.approx(1.0)


def test_malicious_transition_covariance_matches_scaled_sample_covariances() -> None:
    rng = np.random.default_rng(0)
    window_minus = rng.normal(size=(50, 3))
    window_plus = rng.normal(size=(60, 3))
    result = malicious_transition_covariance(window_minus, window_plus)
    expected = np.cov(window_minus, rowvar=False) / 50 + np.cov(window_plus, rowvar=False) / 60
    assert np.allclose(result, expected)


def _synthetic_replicates(
    rng: np.random.Generator, count: int, dimension: int, nuisance_direction: np.ndarray
) -> tuple[list[np.ndarray], list[tuple[int, int]]]:
    displacements = [
        nuisance_direction * rng.normal() + 0.01 * rng.normal(size=dimension) for _ in range(count)
    ]
    supports = [(200, 200) for _ in range(count)]
    return displacements, supports


def test_select_stable_nuisance_rank_finds_the_dominant_direction() -> None:
    rng = np.random.default_rng(1)
    dimension = 6
    nuisance_direction = np.zeros(dimension)
    nuisance_direction[0] = 1.0
    displacements, supports = _synthetic_replicates(rng, 40, dimension, nuisance_direction)
    result = select_stable_nuisance_rank(
        replicate_displacements=displacements,
        replicate_supports=supports,
        dimension=dimension,
        configured_maximum_rank=3,
        eigengap_requirement=2.0,
        rank_clip_epsilon_relative=1e-6,
        scale_standardization_floor=1e-8,
        bootstrap_resamples=50,
        minimum_bootstrap_stability_fraction=0.6,
        seed=42,
    )
    assert result.selected_rank == 1
    assert result.eigengap_ratio > 2.0
    assert result.subspace.shape == (dimension, 1)


def test_bootstrap_malicious_sampling_term_is_nonnegative_and_shrinks_with_sample_size() -> None:
    rng = np.random.default_rng(2)
    dimension = 4
    projector = np.eye(dimension)
    covariance = np.eye(dimension)

    small_minus = rng.normal(size=(20, dimension))
    small_plus = rng.normal(size=(20, dimension))
    small_observed = small_plus.mean(axis=0) - small_minus.mean(axis=0)
    small_term = bootstrap_malicious_sampling_term(
        small_minus, small_plus, small_observed, projector, covariance, 0.1, 200, 7
    )

    large_minus = rng.normal(size=(2000, dimension))
    large_plus = rng.normal(size=(2000, dimension))
    large_observed = large_plus.mean(axis=0) - large_minus.mean(axis=0)
    large_term = bootstrap_malicious_sampling_term(
        large_minus, large_plus, large_observed, projector, covariance, 0.1, 200, 7
    )

    assert small_term >= 0.0
    assert large_term >= 0.0
    assert large_term < small_term


def test_bootstrap_subspace_estimation_term_is_nonnegative() -> None:
    rng = np.random.default_rng(3)
    dimension = 5
    nuisance_direction = np.zeros(dimension)
    nuisance_direction[0] = 1.0
    displacements, supports = _synthetic_replicates(rng, 30, dimension, nuisance_direction)
    reference_projector = np.eye(dimension) - np.outer(nuisance_direction, nuisance_direction)
    term = bootstrap_subspace_estimation_term(
        displacements,
        supports,
        selected_rank=1,
        reference_projector=reference_projector,
        alpha=0.1,
        resamples=100,
        seed=11,
        smallest_malicious_eigenvalue=1.0,
    )
    assert term >= 0.0


def test_control_span_violation_term_is_nonnegative() -> None:
    rng = np.random.default_rng(4)
    dimension = 5
    nuisance_direction = np.zeros(dimension)
    nuisance_direction[0] = 1.0
    displacements, supports = _synthetic_replicates(rng, 12, dimension, nuisance_direction)
    term = control_span_violation_term(
        displacements,
        supports,
        selected_rank=1,
        alpha=0.1,
        smallest_malicious_eigenvalue=1.0,
    )
    assert term >= 0.0


def test_private_transition_term_requires_at_least_two_transitions() -> None:
    projector = np.eye(3)
    assert (
        private_transition_term_single_client([np.zeros(3)], projector, 0.1, 1.0, 1e-6, 100) is None
    )


def test_private_transition_term_is_nonnegative_with_enough_history() -> None:
    rng = np.random.default_rng(5)
    projector = np.eye(3)
    transitions = [rng.normal(size=3) for _ in range(6)]
    term = private_transition_term_single_client(transitions, projector, 0.2, 1.0, 1e-6, 200)
    assert term is not None
    assert term >= 0.0
