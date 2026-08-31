from __future__ import annotations

import numpy as np

from fedact.core.controls import (
    ControlQualityGate,
    ControlReplicate,
    build_control_displacement,
    filter_control_replicates,
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


def test_filter_control_replicates_excludes_outlier_displacements() -> None:
    import torch

    replicates = [
        ControlReplicate(
            replicate_index=i,
            displacement=torch.tensor(displacement),
            support_before=10,
            support_after=10,
        )
        for i, displacement in enumerate(
            [
                [0.0, 0.0],
                [0.1, 0.0],
                [-0.1, 0.0],
                [10.0, 10.0],
            ]
        )
    ]
    gate = ControlQualityGate(held_out_residual_quantile=0.5, minimum_pass_fraction=0.5)
    kept = filter_control_replicates(replicates, gate)
    assert len(kept) < len(replicates)
    assert all(replicate.replicate_index != 3 for replicate in kept)
