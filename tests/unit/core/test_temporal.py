from __future__ import annotations

import numpy as np
import pytest

from fedact.core.temporal import (
    fit_scalar_model,
    process_error_radius,
    propagate_radius,
)


def test_fit_scalar_model_estimates_coefficient() -> None:
    centers = tuple(0.8**i * np.ones(3) for i in range(10))
    fit = fit_scalar_model(centers, maximum_coefficient=0.99)
    assert fit.coefficient == pytest.approx(0.8, abs=1e-2)
    assert fit.residuals.shape[0] == 9


def test_process_error_radius_computes_residual_quantile() -> None:
    residuals = np.array([[float(i), 0.0] for i in range(10)])
    radius = process_error_radius(residuals, quantile=0.9)
    assert radius > 0.0


def test_propagate_radius_grows_over_horizon() -> None:
    r0 = 1.0
    rw = 0.2
    a = 0.9
    r1 = propagate_radius(r0, a, rw, horizon_steps=1)
    r3 = propagate_radius(r0, a, rw, horizon_steps=3)
    assert r3 > r1
