from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class ControlReplicate:
    replicate_index: int
    displacement: FloatArray
    support_before: int
    support_after: int


@dataclass(frozen=True)
class ControlQualityGate:
    held_out_residual_quantile: float
    minimum_pass_fraction: float


def build_control_displacement(mean_before: FloatArray, mean_after: FloatArray) -> FloatArray:
    return mean_after - mean_before


def held_out_reconstruction_residuals(displacements: tuple[FloatArray, ...]) -> tuple[float, ...]:
    residuals: list[float] = []
    for excluded in range(len(displacements)):
        kept = [item for index, item in enumerate(displacements) if index != excluded]
        if not kept:
            raise ValueError("held-out reconstruction requires at least two replicates")
        stacked: FloatArray = np.stack(kept)
        center: FloatArray = stacked.mean(axis=0)
        target = displacements[excluded]
        residual = float(np.linalg.norm(target - center))
        residuals.append(residual)
    return tuple(residuals)


def is_control_gate_passing(
    residuals: tuple[float, ...],
    gate: ControlQualityGate,
) -> bool:
    threshold = float(np.quantile(residuals, gate.held_out_residual_quantile, method="linear"))
    passing = sum(1 for residual in residuals if residual <= threshold)
    fraction = passing / len(residuals)
    return fraction >= gate.minimum_pass_fraction
