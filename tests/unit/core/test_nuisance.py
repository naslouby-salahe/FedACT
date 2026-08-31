from __future__ import annotations

import numpy as np
import pytest

from fedact.core.nuisance import (
    admissible_rank,
    eigengap_ratio,
    is_rank_stable,
    regularized_covariance,
    select_rank_by_eigengap,
    weighted_covariance,
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


def test_is_rank_stable_checks_bootstrap_fraction() -> None:
    assert is_rank_stable((3,) * 85 + (2,) * 15, full_sample_rank=3, minimum_fraction=0.8)
    assert not is_rank_stable((3,) * 70 + (2,) * 30, full_sample_rank=3, minimum_fraction=0.8)


def test_regularized_covariance_adds_scaled_identity() -> None:
    cov = np.eye(3)
    reg = regularized_covariance(cov, coefficient=0.01, floor=1e-6)
    assert float(reg[0, 0]) == pytest.approx(1.01)
