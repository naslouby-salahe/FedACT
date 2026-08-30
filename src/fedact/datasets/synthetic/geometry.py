from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import numpy as np
from numpy.typing import NDArray
from pydantic import Field

FloatArray = NDArray[np.float64]
Tolerance = Annotated[float, Field(gt=0.0)]
AngleDegrees = Annotated[float, Field(ge=0.0, le=360.0)]


def _norm(vector: NDArray[np.float64]) -> float:
    return float(np.sqrt(np.sum(vector * vector)))


class GeometryValidationError(ValueError):
    pass


def verify_orthonormality(basis: np.ndarray, tolerance: Tolerance) -> None:
    residual = float(np.max(np.abs(basis.T @ basis - np.eye(basis.shape[1]))))
    if residual > tolerance:
        raise GeometryValidationError(
            f"nuisance basis is not orthonormal within tolerance {tolerance}: {residual}"
        )


def common_intersection_dimension(
    bases: tuple[np.ndarray, ...], rank_tolerance: Tolerance
) -> Annotated[int, Field(ge=0)]:
    stacked = np.concatenate(bases, axis=1)
    singular_values = np.linalg.svd(stacked, compute_uv=False)
    if singular_values.size == 0:
        return 0
    cutoff = max(singular_values[0], 1.0) * rank_tolerance
    return int(np.count_nonzero(singular_values > cutoff))


def principal_angles(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    overlap = first.T @ second
    singular_values = np.linalg.svd(overlap, compute_uv=False)
    cosine = np.clip(singular_values, -1.0, 1.0)
    return np.arccos(cosine)


@dataclass(frozen=True)
class ActionGeometry:
    range_direction: np.ndarray
    null_direction: np.ndarray


def action_rotation(
    range_direction: np.ndarray, null_direction: np.ndarray, angle_degrees: AngleDegrees
) -> np.ndarray:
    theta = np.deg2rad(angle_degrees)
    rotated = np.cos(theta) * range_direction + np.sin(theta) * null_direction
    norm = _norm(rotated)
    if norm < 1e-12:
        raise GeometryValidationError("action rotation produced a zero direction")
    return rotated / norm


ActionScore = Annotated[float, Field()]


def true_action_score(direction: np.ndarray, transition: np.ndarray) -> ActionScore:
    return float(direction @ transition)


ConditioningRatio = Annotated[float, Field(ge=0.0, le=1.0)]


def spectral_conditioning_ratio(singular_values: np.ndarray) -> ConditioningRatio:
    positive = singular_values[singular_values > 0]
    if positive.size < 2:
        raise GeometryValidationError(
            "spectral conditioning requires at least two nonzero singular values"
        )
    ratio = positive.min() / positive.max()
    return float(ratio * ratio)
