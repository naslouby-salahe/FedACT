from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, NewType

import numpy as np
from numpy.typing import NDArray
from pydantic import Field

FloatArray = NDArray[np.float64]
EmbeddingVector = NewType("EmbeddingVector", FloatArray)
SYNTHETIC_DIMENSION = 64

DisplacementNorm = Annotated[float, Field(ge=0.0)]
EigenValue = Annotated[float, Field()]
Width = Annotated[float, Field(ge=0.0)]
TauAlign = Annotated[float, Field()]
TauAmb = Annotated[float, Field(gt=0.0)]
EpsilonRelative = Annotated[float, Field(gt=0.0)]
ConditioningIndex = Annotated[float, Field(ge=0.0)]


@dataclass(frozen=True)
class DomainValidity:
    domain_valid: bool


class DecisionState(StrEnum):
    POSITIVELY_IDENTIFIED = "POSITIVELY_IDENTIFIED"
    NEGATIVELY_IDENTIFIED = "NEGATIVELY_IDENTIFIED"
    AMBIGUOUS = "AMBIGUOUS"


class NumericalFailureError(ValueError):
    pass


def projector_from_basis(basis: FloatArray) -> FloatArray:
    return np.eye(basis.shape[0]) - basis @ basis.T


def whiten(covariance: FloatArray) -> FloatArray:
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    if float(eigenvalues.min()) <= 0.0:
        raise NumericalFailureError("covariance is not positive definite; cannot whiten")
    return eigenvectors @ np.diag(1.0 / np.sqrt(eigenvalues)) @ eigenvectors.T


@dataclass(frozen=True)
class ActionDisplacementEvaluation:
    displacement: EmbeddingVector

    def displacement_norm(self) -> DisplacementNorm:
        squared = float(self.displacement @ self.displacement)
        value: DisplacementNorm = squared**0.5
        return value

    def unit_direction(self) -> EmbeddingVector:
        norm = self.displacement_norm()
        if norm == 0.0:
            raise NumericalFailureError("zero displacement has no direction")
        return EmbeddingVector(self.displacement / norm)


@dataclass(frozen=True)
class ActionInterval:
    lower: float
    upper: float

    def __post_init__(self) -> None:
        if self.lower > self.upper:
            raise NumericalFailureError(
                f"action interval lower bound {self.lower} exceeds upper bound {self.upper}"
            )

    @property
    def interval_width(self) -> Width:
        value: Width = self.upper - self.lower
        return value


def support_interval(
    direction: FloatArray, feasible_set_vertices: tuple[FloatArray, ...]
) -> ActionInterval:
    if not feasible_set_vertices:
        raise NumericalFailureError("support interval requires at least one feasible point")
    projections = [float(direction @ vertex) for vertex in feasible_set_vertices]
    return ActionInterval(lower=min(projections), upper=max(projections))


def classify_decision_state(interval: ActionInterval, tau_align: TauAlign) -> DecisionState:
    if interval.lower >= tau_align:
        return DecisionState.POSITIVELY_IDENTIFIED
    if interval.upper < tau_align:
        return DecisionState.NEGATIVELY_IDENTIFIED
    return DecisionState.AMBIGUOUS


def is_certified(
    state: DecisionState,
    interval: ActionInterval,
    tau_amb: TauAmb,
    validity: DomainValidity,
) -> bool:
    return (
        state is DecisionState.POSITIVELY_IDENTIFIED
        and interval.interval_width <= tau_amb
        and validity.domain_valid
    )


def action_conditioning_index(
    direction: FloatArray, information: FloatArray
) -> ConditioningIndex | None:
    pinv = np.linalg.pinv(information)
    value = float(direction @ pinv @ direction)
    if value <= 0.0 or not np.isfinite(value):
        return None
    result: ConditioningIndex = float(np.sqrt(value))
    return result


def smallest_positive_eigenvalue(
    information: FloatArray, rank_epsilon_relative: EpsilonRelative
) -> EigenValue | None:
    eigenvalues = np.linalg.eigvalsh(information)
    largest = float(eigenvalues.max())
    cutoff = rank_epsilon_relative * largest
    positive = eigenvalues[eigenvalues > cutoff]
    if positive.size == 0:
        return None
    result: EigenValue = float(positive.min())
    return result
