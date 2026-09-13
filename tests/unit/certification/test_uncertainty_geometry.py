from __future__ import annotations

import numpy as np
import pytest
import torch

from fedact.certification.certificate import FeasibleSet
from fedact.certification.uncertainty import (
    admissible_rank,
    client_radius,
    eigengap_ratio,
    is_rank_stable,
    regularized_covariance,
    sampling_uncertainty_quantile,
    select_rank_by_eigengap,
    solve_action_interval,
    solve_support_bounds,
    standardized_subspace_term,
    subspace_uncertainty,
    weighted_covariance,
)

SPECTRUM = [4.0, 3.0, 2.0, 1.0]
ALPHA = 0.05
CLIP_RELATIVE = 1.0e-6
FLOOR = 1.0e-9


def test_weighted_covariance_of_a_single_sample_is_the_identity() -> None:
    assert np.allclose(weighted_covariance(np.array([[1.0, 2.0]])), np.eye(2))


def test_weighted_covariance_of_a_sequence_matches_numpy_covariance() -> None:
    samples = [np.array([0.0, 1.0]), np.array([1.0, 3.0]), np.array([2.0, 5.0])]
    assert np.allclose(weighted_covariance(samples), np.cov(np.stack(samples), rowvar=False))


def test_weighted_covariance_honours_weights() -> None:
    samples = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 0.0]])
    weighted = weighted_covariance(samples, (0.0, 0.5, 0.5))
    unweighted = weighted_covariance(samples)
    assert not np.allclose(weighted, unweighted)
    assert np.allclose(weighted, weighted.T)


def test_regularized_covariance_falls_back_to_the_primary_coefficient() -> None:
    covariance = np.zeros((2, 2))
    assert np.allclose(regularized_covariance(covariance, 0.01, 1.0e-9), 0.01 * np.eye(2))


def test_regularized_covariance_applies_the_floor_over_a_smaller_override() -> None:
    covariance = np.zeros((2, 2))
    regularized = regularized_covariance(covariance, 0.01, 0.5, regularization=0.1)
    assert np.allclose(regularized, 0.5 * np.eye(2))


def test_admissible_rank_minimises_over_the_supplied_bounds() -> None:
    assert admissible_rank(dimension=8, replicates=5, configured_maximum=6) == 4


def test_admissible_rank_uses_the_variance_threshold_when_supplied() -> None:
    assert admissible_rank(spectrum=[4.0, 1.0, 1.0, 1.0], variance_threshold=0.5) == 1
    assert admissible_rank(spectrum=[4.0, 1.0, 1.0, 1.0], variance_threshold=0.99) == 4


def test_admissible_rank_of_a_degenerate_spectrum_is_one() -> None:
    assert admissible_rank(spectrum=[0.0, 0.0], variance_threshold=0.5) == 1


def test_admissible_rank_without_any_input_defaults_to_one() -> None:
    assert admissible_rank() == 1


def test_eigengap_ratio_is_neutral_outside_the_spectrum() -> None:
    assert eigengap_ratio(SPECTRUM, rank=0, clip_relative=CLIP_RELATIVE, floor=FLOOR) == 1.0
    assert (
        eigengap_ratio(SPECTRUM, rank=len(SPECTRUM), clip_relative=CLIP_RELATIVE, floor=FLOOR)
        == 1.0
    )


def test_eigengap_ratio_divides_by_the_clipped_denominator() -> None:
    assert eigengap_ratio(
        SPECTRUM, rank=1, clip_relative=CLIP_RELATIVE, floor=FLOOR
    ) == pytest.approx(4.0 / 3.0)


def test_select_rank_by_eigengap_prefers_the_admissible_ceiling() -> None:
    assert select_rank_by_eigengap(SPECTRUM, 1.0, CLIP_RELATIVE, FLOOR, maximum_admissible=2) <= 2
    assert select_rank_by_eigengap(SPECTRUM, 1.0, CLIP_RELATIVE, FLOOR, maximum_rank=1) <= 1
    assert select_rank_by_eigengap(SPECTRUM, 1.0, CLIP_RELATIVE, FLOOR) <= len(SPECTRUM) - 1


def test_rank_stability_against_a_full_sample_rank_uses_the_fraction() -> None:
    assert is_rank_stable((2, 2, 2, 3), 0.5, full_sample_rank=2) is True
    assert is_rank_stable((3, 3, 3, 3), 0.5, full_sample_rank=2) is False
    assert is_rank_stable((), 0.5, full_sample_rank=2) is False


def test_rank_stability_without_a_reference_requires_a_single_rank() -> None:
    assert is_rank_stable((2, 2, 2), 0.5) is True
    assert is_rank_stable((2, 3, 2), 0.5) is False


def test_sampling_uncertainty_requires_bootstrap_draws() -> None:
    with pytest.raises(ValueError, match="requires bootstrap draws"):
        sampling_uncertainty_quantile((), ALPHA)


def test_sampling_uncertainty_is_the_upper_bootstrap_quantile() -> None:
    draws = (1.0, 2.0, 3.0, 4.0)
    assert sampling_uncertainty_quantile(draws, 0.25) == pytest.approx(
        float(np.quantile(draws, 0.75, method="linear"))
    )


def test_subspace_uncertainty_quantifies_projection_drift() -> None:
    reference = np.eye(2)
    perturbed = (np.eye(2), np.array([[1.0, 1.0], [0.0, 1.0]]))
    uncertainty = subspace_uncertainty(perturbed, reference, 0.5)
    assert uncertainty >= 0.0
    assert uncertainty <= 1.0


def test_standardized_subspace_term_requires_a_positive_eigenvalue() -> None:
    with pytest.raises(ValueError, match="positive minimal eigenvalue"):
        standardized_subspace_term(0.1, 0.2, 0.0)


def test_standardized_subspace_term_divides_by_the_square_root() -> None:
    assert standardized_subspace_term(0.2, 0.5, 4.0) == pytest.approx(0.2 * 0.5 / 2.0)


def test_client_radius_is_the_sum_of_its_contributions() -> None:
    assert client_radius(0.1, 0.2, 0.3, 0.4) == pytest.approx(1.0)


def test_support_bounds_require_nonempty_constraint_limits() -> None:
    with pytest.raises(ValueError, match="nonempty constraint limits"):
        solve_support_bounds(np.array([1.0, 0.0]), np.zeros((0, 2)), np.array([]))


def test_support_bounds_scale_with_the_direction_norm() -> None:
    interval = solve_support_bounds(np.array([3.0, 4.0]), np.zeros((1, 2)), np.array([2.0]))
    assert interval.lower == pytest.approx(-10.0)
    assert interval.upper == pytest.approx(10.0)


def _feasible_set(uncertainty_radii: tuple[float, ...]) -> FeasibleSet:
    return FeasibleSet(
        nuisance_subspaces=(torch.zeros((2, 2)),),
        uncertainty_radii=uncertainty_radii,
        diameter=1.0,
    )


def test_action_interval_requires_client_uncertainty_radii() -> None:
    with pytest.raises(ValueError, match="require client uncertainty radii"):
        solve_action_interval(torch.tensor([1.0, 0.0]), _feasible_set(()))


def test_action_interval_is_centred_on_the_action_norm() -> None:
    interval = solve_action_interval(torch.tensor([3.0, 4.0]), _feasible_set((0.5, 0.25)))
    assert interval.lower == pytest.approx(5.0 - 0.75)
    assert interval.upper == pytest.approx(5.0 + 0.75)


def test_action_interval_of_an_empty_action_vector_is_zero_centred() -> None:
    interval = solve_action_interval(torch.zeros(0), _feasible_set((0.5,)))
    assert interval.lower == pytest.approx(-0.5)
    assert interval.upper == pytest.approx(0.5)
