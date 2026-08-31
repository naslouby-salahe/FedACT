from __future__ import annotations

import numpy as np
import pytest

from fedact.core.solver import SolverToleranceSettings, solve_support_bounds

SETTINGS = SolverToleranceSettings(
    relative_tolerance=1e-8,
    absolute_tolerance=1e-8,
    duality_gap_tolerance=1e-8,
    maximum_iterations=200,
)


def test_solve_support_bounds_on_box() -> None:
    direction = np.array([1.0, 0.0])
    coeffs = np.array([[1.0, 0.0], [-1.0, 0.0], [0.0, 1.0], [0.0, -1.0]])
    limits = np.array([2.0, 2.0, 2.0, 2.0])
    interval = solve_support_bounds(
        direction=direction,
        constraint_coefficients=coeffs,
        constraint_limits=limits,
        settings=SETTINGS,
    )
    assert interval.lower == pytest.approx(-2.0, abs=1e-4)
    assert interval.upper == pytest.approx(2.0, abs=1e-4)
