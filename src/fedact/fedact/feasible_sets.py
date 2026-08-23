from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import numpy as np
from pydantic import Field

from fedact.fedact.estimand import FloatArray, NumericalFailureError

Tolerance = Annotated[float, Field(gt=0.0)]

Radius = Annotated[float, Field(gt=0.0)]
ScalarCoefficient = Annotated[float, Field()]


@dataclass(frozen=True)
class L2Ball:
    center: FloatArray
    radius: Radius

    def __post_init__(self) -> None:
        if self.radius <= 0.0:
            raise NumericalFailureError("L2 ball radius must be positive")

    def is_containing(self, point: FloatArray, tolerance: Tolerance) -> bool:
        return float(np.linalg.norm(point - self.center)) <= self.radius + tolerance


@dataclass(frozen=True)
class ClientConstraint:
    projector: FloatArray
    covariance: FloatArray
    beta: Radius
    client_index: int


def is_constraint_satisfied(constraint: ClientConstraint, point: FloatArray) -> bool:
    whitened = _whitened_norm(constraint.covariance, point)
    return whitened <= constraint.beta + 1e-12


def _whitened_norm(covariance: FloatArray, vector: FloatArray) -> float:
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    if float(eigenvalues.min()) <= 0.0:
        raise NumericalFailureError("client covariance must be positive definite")
    transformed = eigenvectors.T @ vector
    scaled = transformed / np.sqrt(eigenvalues)
    return float(np.linalg.norm(scaled))


SampleVertices = Annotated[int, Field(ge=1)]


def intersect_constraints(
    plausibility: L2Ball,
    constraints: tuple[ClientConstraint, ...],
    vertices: SampleVertices = 4096,
) -> FloatArray | None:
    dimension = plausibility.center.shape[0]
    generator = np.random.default_rng(20240101)
    samples = generator.standard_normal((vertices, dimension))
    samples /= np.linalg.norm(samples, axis=1, keepdims=True)
    candidates = plausibility.center + plausibility.radius * samples
    for constraint in constraints:
        keep = np.array(
            [
                _whitened_norm(constraint.covariance, point) <= constraint.beta
                for point in candidates
            ]
        )
        candidates = candidates[keep]
        if candidates.size == 0:
            return None
    return candidates


def chebyshev_center(feasible_points: FloatArray) -> tuple[FloatArray, Radius]:
    center = feasible_points.mean(axis=0)
    distances = np.linalg.norm(feasible_points - center, axis=1)
    value: Radius = float(np.min(distances))
    if value <= 0.0:
        raise NumericalFailureError("degenerate feasible set has no interior ball")
    return center, value


def minimum_uniform_inflation(
    plausibility: L2Ball,
    constraints: tuple[ClientConstraint, ...],
    vertices: SampleVertices,
) -> Radius:
    dimension = plausibility.center.shape[0]
    generator = np.random.default_rng(20240101)
    samples = generator.standard_normal((vertices, dimension))
    samples /= np.linalg.norm(samples, axis=1, keepdims=True)
    candidates = plausibility.center + plausibility.radius * samples
    worst = 1.0
    for point in candidates:
        for constraint in constraints:
            violation = _whitened_norm(constraint.covariance, point)
            if violation > constraint.beta:
                worst = max(worst, violation / constraint.beta)
    result: Radius = worst
    return result
