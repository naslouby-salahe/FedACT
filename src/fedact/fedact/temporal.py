from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import numpy as np
from pydantic import Field

from fedact.fedact.estimand import FloatArray, NumericalFailureError

ProcessRadius = Annotated[float, Field(gt=0.0)]
ScalarCoefficient = Annotated[float, Field()]


@dataclass(frozen=True)
class TemporalModel:
    scalar_coefficient: float
    process_error_radius: float
    consecutive_pairs_used: int


def fit_scalar_model(
    centers: tuple[FloatArray, ...], maximum_coefficient: ScalarCoefficient
) -> tuple[ScalarCoefficient, FloatArray]:
    if len(centers) < 2:
        raise NumericalFailureError("temporal model fitting requires at least two centers")
    numerators = [float(u @ v) for u, v in zip(centers[:-1], centers[1:], strict=True)]
    denominators = [float(u @ u) for u in centers[:-1]]
    denominator_sum = sum(denominators)
    if denominator_sum <= 0.0:
        raise NumericalFailureError("temporal fit denominator at or below the floor")
    raw = sum(numerators) / denominator_sum
    coefficient = min(maximum_coefficient, max(0.0, raw))
    residuals = np.array(
        [centers[i + 1] - coefficient * centers[i] for i in range(len(centers) - 1)]
    )
    return coefficient, residuals


def process_error_radius(
    residuals: FloatArray, quantile: Annotated[float, Field(gt=0.0, le=1.0)]
) -> ProcessRadius:
    norms = np.linalg.norm(residuals, axis=1)
    value: ProcessRadius = float(np.quantile(norms, quantile, method="linear"))
    return value


SetRadius = Annotated[float, Field(ge=0.0)]
HorizonSteps = Annotated[int, Field(ge=1)]


def propagate_radius(
    initial_set_radius: SetRadius,
    coefficient: ScalarCoefficient,
    process_radius: ProcessRadius,
    horizon_steps: HorizonSteps,
) -> SetRadius:
    if horizon_steps < 1:
        raise NumericalFailureError("propagation requires at least one step")
    accumulated_process = process_radius * sum(coefficient**step for step in range(horizon_steps))
    return (coefficient**horizon_steps) * initial_set_radius + accumulated_process
