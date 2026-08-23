from __future__ import annotations

import numpy as np

from fedact.baselines.identification import (
    covariance_weighted_reconstruction,
    matched_benign_subtraction,
    projected_point_reconstruction,
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
    res = covariance_weighted_reconstruction(mal, cov)
    assert res.estimated_displacement.shape == (2,)
