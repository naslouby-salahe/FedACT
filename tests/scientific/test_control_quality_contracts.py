from __future__ import annotations

import numpy as np

from fedact.fedact.controls import (
    ControlQualityGate,
    held_out_reconstruction_residuals,
    is_control_gate_passing,
)


def test_control_quality_gate_passes_for_low_residuals() -> None:
    replicates = (
        np.array([1.0, 0.0, 0.0, 0.0]),
        np.array([1.0, 0.0, 0.0, 0.0]),
        np.array([1.0, 0.0, 0.0, 0.0]),
    )
    residuals = held_out_reconstruction_residuals(replicates)
    gate = ControlQualityGate(held_out_residual_quantile=0.75, minimum_pass_fraction=0.8)
    assert is_control_gate_passing(residuals, gate)
