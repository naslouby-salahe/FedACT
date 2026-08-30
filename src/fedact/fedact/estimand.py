from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch

from fedact.domain.enums import ActionPolarity
from fedact.domain.types import (
    AmbiguityFlag,
    CertificationFlag,
    CoordinateValue,
    IntervalBound,
    ThresholdValue,
)


class NumericalFailureError(RuntimeError):
    pass


@dataclass(frozen=True)
class ActionInterval:
    lower: IntervalBound
    upper: IntervalBound

    def __post_init__(self) -> None:
        if self.lower > self.upper:
            raise NumericalFailureError(
                f"Inverted interval: lower ({self.lower}) > upper ({self.upper})"
            )

    @property
    def width(self) -> IntervalBound:
        return float(self.upper - self.lower)

    @property
    def interval_width(self) -> IntervalBound:
        return float(self.upper - self.lower)

    def is_certified_positive(
        self, threshold: ThresholdValue, ambiguity_width: ThresholdValue
    ) -> CertificationFlag:
        return self.lower >= threshold and self.width <= ambiguity_width

    def is_certified_negative(
        self, threshold: ThresholdValue, ambiguity_width: ThresholdValue
    ) -> CertificationFlag:
        return self.upper < threshold and self.width <= ambiguity_width

    def is_ambiguous(
        self, threshold: ThresholdValue, ambiguity_width: ThresholdValue
    ) -> AmbiguityFlag:
        return self.lower < threshold <= self.upper or self.width > ambiguity_width


def projector_from_basis(basis: np.ndarray | torch.Tensor) -> np.ndarray:
    b = np.array(basis) if isinstance(basis, torch.Tensor) else basis
    d = b.shape[0]
    if b.size == 0 or b.shape[1] == 0:
        return np.eye(d)
    q, _unused = np.linalg.qr(b)
    return np.eye(d) - q @ q.T


def support_interval(
    direction: np.ndarray | torch.Tensor,
    vertices: Sequence[np.ndarray | torch.Tensor],
) -> ActionInterval:
    if not vertices:
        return ActionInterval(lower=0.0, upper=0.0)
    d = np.array(direction) if isinstance(direction, torch.Tensor) else direction
    values = [float(np.dot(d, np.array(v) if isinstance(v, torch.Tensor) else v)) for v in vertices]
    return ActionInterval(lower=min(values), upper=max(values))


def smallest_positive_eigenvalue(
    matrix: np.ndarray | torch.Tensor,
    tolerance: ThresholdValue,
    rank_epsilon_relative: ThresholdValue,
) -> CoordinateValue | None:
    m = np.array(matrix) if isinstance(matrix, torch.Tensor) else matrix
    eigs = np.linalg.eigvalsh(m)
    max_eig = float(np.max(eigs)) if eigs.size > 0 else 0.0
    if max_eig < tolerance:
        return None
    cutoff = max(1e-12, float(max_eig * rank_epsilon_relative))
    pos = [float(ev) for ev in eigs if ev > cutoff]
    return min(pos) if pos else None


def action_conditioning_index(
    action: np.ndarray | torch.Tensor,
    information_matrix: np.ndarray | torch.Tensor,
) -> CoordinateValue | None:
    a = np.array(action) if isinstance(action, torch.Tensor) else action
    norm = float(np.linalg.norm(a))
    if norm < 1e-12:
        return None
    u = a / norm
    h = (
        np.array(information_matrix)
        if isinstance(information_matrix, torch.Tensor)
        else information_matrix
    )
    return float(u.T @ h @ u)


def classify_action_interval(
    interval: ActionInterval,
    alignment_threshold: ThresholdValue,
    ambiguity_width: ThresholdValue,
) -> ActionPolarity:
    if interval.is_certified_positive(alignment_threshold, ambiguity_width):
        return ActionPolarity.POSITIVE
    if interval.is_certified_negative(alignment_threshold, ambiguity_width):
        return ActionPolarity.NEGATIVE
    return ActionPolarity.AMBIGUOUS
