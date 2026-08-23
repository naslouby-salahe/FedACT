from __future__ import annotations

import numpy as np

from fedact.fedact.controls import (
    ControlQualityGate,
    build_control_displacement,
    held_out_reconstruction_residuals,
    is_control_gate_passing,
)


def test_build_control_displacement_aggregates_half_open_windows() -> None:
    prior = np.ones(4)
    recent = 2.0 * np.ones(4)
    delta = build_control_displacement(prior, recent)
    assert np.allclose(delta, 1.0)


def test_held_out_reconstruction_residuals() -> None:
    replicates = (
        np.array([1.0, 0.0, 0.0, 0.0]),
        np.array([0.0, 0.0, 1.0, 0.0]),
        np.array([0.0, 0.0, 0.0, 1.0]),
    )
    residuals = held_out_reconstruction_residuals(replicates)
    assert len(residuals) == 3


def test_is_control_gate_passing() -> None:
    gate = ControlQualityGate(held_out_residual_quantile=0.5, minimum_pass_fraction=0.5)
    residuals = (0.1, 0.2, 0.3, 0.4)
    assert is_control_gate_passing(residuals, gate)
