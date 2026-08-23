from __future__ import annotations

import numpy as np
import pytest

from fedact.experiments.math_verification import (
    is_constraint_monotone,
    is_degenerate_rejection_correct,
    is_diameter_upper_bound_valid,
    is_functionally_identifiable,
    null_space_basis,
    run_mathematical_verification,
    verify_action_width_bound,
)
from fedact.fedact.feasible_sets import L2Ball


def test_null_space_basis_spans_the_kernel() -> None:
    matrix = np.array([[1.0, 0.0, 0.0], [0.0, 0.0, 0.0]])
    kernel = null_space_basis(matrix)
    assert kernel.shape == (3, 2)
    assert matrix @ kernel == pytest.approx(np.zeros((2, 2)), abs=1e-12)


def test_functional_identifiability_inside_and_outside_range() -> None:
    stacked = np.vstack([np.eye(4)[:3], np.zeros((1, 4))])
    assert is_functionally_identifiable(np.array([1.0, 0.0, 0.0, 0.0]), stacked)
    assert not is_functionally_identifiable(np.array([0.0, 0.0, 0.0, 1.0]), stacked)


def test_action_width_bound_holds_on_analytical_case() -> None:
    direction = np.array([1.0])
    information = np.array([[4.0]])
    observed, bound = verify_action_width_bound(direction, information, epsilon=0.5)
    assert observed <= bound


def test_degenerate_and_monotonicity_checks() -> None:
    assert is_degenerate_rejection_correct(1e-14, 1e-10)
    direction = np.array([1.0, 0.0])
    outer = tuple(np.array(p) for p in [(2.0, -1.0), (-2.0, -1.0), (2.0, 1.0), (-2.0, 1.0)])
    inner = tuple(np.array(p) for p in [(1.0, -0.5), (-1.0, -0.5), (1.0, 0.5), (-1.0, 0.5)])
    assert is_constraint_monotone(direction, outer, inner)


def test_diameter_bound_validity() -> None:
    ball = L2Ball(center=np.zeros(3), radius=2.0)
    assert is_diameter_upper_bound_valid(ball)


def test_run_mathematical_verification_passes_all_obligations() -> None:
    report = run_mathematical_verification()
    assert report.is_passing
    assert report.scientific_outcome.value == "PASS"
