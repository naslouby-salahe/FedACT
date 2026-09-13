from __future__ import annotations

import numpy as np
import pytest
import torch

from fedact.certification.dynamics import (
    ControlQualityGate,
    ControlReplicate,
    build_control_displacement,
    effective_support,
    filter_control_replicates,
    fit_scalar_model,
    geometric_median,
    held_out_reconstruction_residuals,
    is_control_gate_passing,
    process_error_radius,
    propagate_radius,
    weighted_control_center,
)

GATE = ControlQualityGate(held_out_residual_quantile=0.75, minimum_pass_fraction=0.5)
TOLERANCE = 1.0e-9
MAXIMUM_ITERATIONS = 50


def _replicate(index: int, displacement: list[float]) -> ControlReplicate:
    return ControlReplicate(
        replicate_index=index,
        displacement=torch.tensor(displacement, dtype=torch.float64),
        support_before=10,
        support_after=10,
    )


def test_control_displacement_accepts_numpy_and_torch_inputs() -> None:
    prior = np.array([1.0, 1.0])
    recent = np.array([2.0, 3.0])
    assert np.allclose(build_control_displacement(prior, recent), np.array([1.0, 2.0]))
    assert np.allclose(
        build_control_displacement(torch.tensor(prior), torch.tensor(recent)),
        np.array([1.0, 2.0]),
    )


def test_held_out_residuals_of_no_replicates_is_empty() -> None:
    assert held_out_reconstruction_residuals([]) == ()


def test_held_out_residuals_measure_distance_from_the_mean() -> None:
    residuals = held_out_reconstruction_residuals(
        [np.array([0.0, 0.0]), np.array([2.0, 0.0]), np.array([1.0, 0.0])]
    )
    assert len(residuals) == 3
    assert residuals[1] == pytest.approx(1.0)


def test_control_gate_rejects_an_empty_residual_set() -> None:
    assert is_control_gate_passing([], GATE) is False


def test_control_gate_passes_when_enough_residuals_fall_below_the_quantile() -> None:
    assert is_control_gate_passing([0.1, 0.2, 0.3, 0.4], GATE) is True


def test_filtering_no_replicates_returns_an_empty_tuple() -> None:
    assert filter_control_replicates([], GATE) == ()


def test_filtering_keeps_only_replicates_below_the_residual_quantile() -> None:
    replicates = [
        _replicate(0, [0.0, 0.0]),
        _replicate(1, [1.0, 0.0]),
        _replicate(2, [50.0, 0.0]),
    ]
    kept = filter_control_replicates(replicates, GATE)
    assert len(kept) < len(replicates)
    assert all(replicate.replicate_index != 2 for replicate in kept)


def test_scalar_model_requires_two_centers() -> None:
    with pytest.raises(ValueError, match="at least two temporal centers"):
        fit_scalar_model([np.array([1.0])], 0.99)


def test_scalar_model_requires_historical_variation() -> None:
    with pytest.raises(ValueError, match="nonzero historical variation"):
        fit_scalar_model([np.zeros(2), np.zeros(2)], 0.99)


def test_scalar_model_clamps_the_coefficient_into_range() -> None:
    rising = fit_scalar_model([np.array([1.0]), np.array([2.0]), np.array([4.0])], 0.99)
    assert 0.0 <= rising.coefficient <= 0.99
    assert rising.residuals.shape[0] == 2


def test_process_error_radius_requires_residuals() -> None:
    with pytest.raises(ValueError, match="requires observed temporal residuals"):
        process_error_radius(np.zeros((0, 2)), 0.95)


def test_process_error_radius_is_a_quantile_of_residual_norms() -> None:
    residuals = np.array([[3.0, 4.0], [0.0, 0.0]])
    assert process_error_radius(residuals, 1.0) == pytest.approx(5.0)


def test_radius_propagation_compounds_the_coefficient() -> None:
    assert propagate_radius(1.0, 0.5, 0.25, 2) == pytest.approx(0.625)
    assert propagate_radius(3.0, 0.5, 0.25, 0) == pytest.approx(3.0)


def test_effective_support_combines_two_counts_harmonically() -> None:
    assert effective_support(3, 6) == pytest.approx(2.0)
    assert effective_support((3, 6)) == pytest.approx(2.0)


def test_effective_support_sums_a_sequence() -> None:
    assert effective_support([1, 2, 3]) == pytest.approx(6.0)


def test_effective_support_of_no_arguments_is_zero() -> None:
    assert effective_support() == pytest.approx(0.0)


def test_geometric_median_of_a_single_point_is_that_point() -> None:
    assert np.allclose(
        geometric_median(np.array([1.0, 2.0]), TOLERANCE, MAXIMUM_ITERATIONS), [1.0, 2.0]
    )


def test_geometric_median_of_one_row_returns_the_row() -> None:
    assert np.allclose(
        geometric_median(np.array([[1.0, 2.0]]), TOLERANCE, MAXIMUM_ITERATIONS), [1.0, 2.0]
    )


def test_geometric_median_returns_a_point_that_coincides_with_the_estimate() -> None:
    points = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]])
    assert np.allclose(geometric_median(points, TOLERANCE, MAXIMUM_ITERATIONS), [1.0, 0.0])


def test_geometric_median_converges_within_the_iteration_budget() -> None:
    points = [np.array([0.0, 0.0]), np.array([1.0, 2.0]), np.array([3.0, 1.0])]
    median = geometric_median(points, 1.0, MAXIMUM_ITERATIONS)
    assert median.shape == (2,)


def test_weighted_control_center_of_no_controls_is_a_scalar_zero() -> None:
    assert np.allclose(weighted_control_center([]), np.zeros(1))


def test_weighted_control_center_without_weights_is_the_mean() -> None:
    controls = [np.array([0.0, 0.0]), np.array([2.0, 4.0])]
    assert np.allclose(weighted_control_center(controls), np.array([1.0, 2.0]))


def test_weighted_control_center_accepts_pair_weights() -> None:
    controls = [np.array([0.0]), np.array([10.0])]
    center = weighted_control_center(controls, [(1, 1), (1, 1)])
    assert center.shape == (1,)
    assert 0.0 <= center[0] <= 10.0


def test_weighted_control_center_falls_back_to_the_mean_when_weights_vanish() -> None:
    controls = [np.array([2.0]), np.array([4.0])]
    assert np.allclose(weighted_control_center(controls, [0.0, 0.0]), np.array([3.0]))
