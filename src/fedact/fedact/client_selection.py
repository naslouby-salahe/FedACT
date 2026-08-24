from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Annotated

import numpy as np
from numpy.typing import NDArray
from pydantic import Field

from fedact.domain.types import MetricRate, SampleCount

FloatArray = NDArray[np.float64]
Ridge = Annotated[float, Field(gt=0.0)]
LogDeterminantGain = Annotated[float, Field()]
ActionCount = Annotated[int, Field(ge=0)]
SelectedCount = Annotated[int, Field(ge=1)]


@dataclass(frozen=True)
class SelectionBudget:
    budget_fraction: MetricRate
    eligible_clients: SampleCount

    @property
    def selected_count(self) -> SelectedCount:
        raw = math.ceil(self.budget_fraction * self.eligible_clients)
        value: SelectedCount = max(1, min(self.eligible_clients, raw))
        return value


def d_optimal_gain(
    current_sum: FloatArray, candidate: FloatArray, ridge_lambda: Ridge
) -> LogDeterminantGain:
    identity = np.eye(current_sum.shape[0])
    combined = current_sum + candidate + ridge_lambda * identity
    base = current_sum + ridge_lambda * identity
    sign_combined, logdet_combined = np.linalg.slogdet(combined)
    sign_base, logdet_base = np.linalg.slogdet(base)
    if sign_combined <= 0 or sign_base <= 0:
        raise ValueError("information matrices must stay positive definite")
    value: LogDeterminantGain = float(logdet_combined - logdet_base)
    return value


def greedy_d_optimal(
    information_matrices: dict[str, FloatArray],
    ridge_lambda: Ridge,
    budget: SelectionBudget,
) -> tuple[str, ...]:
    selected: list[str] = []
    remaining = sorted(information_matrices)
    dimension = next(iter(information_matrices.values())).shape[0]
    accumulated: FloatArray = np.zeros((dimension, dimension))
    while len(selected) < budget.selected_count and remaining:
        gains = {
            name: d_optimal_gain(accumulated, information_matrices[name], ridge_lambda)
            for name in remaining
        }
        best = min(gains.items(), key=lambda item: (-item[1], item[0]))[0]
        selected.append(best)
        remaining.remove(best)
        accumulated = accumulated + information_matrices[best]
    return tuple(selected)


def uniform_action_weights(action_count: ActionCount) -> tuple[float, ...]:
    if action_count == 0:
        return ()
    weight = 1.0 / action_count
    return tuple(weight for _ in range(action_count))
