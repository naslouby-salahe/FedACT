from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import torch
from numpy.typing import NDArray

from fedact.certification.certificate import ClientConstraint, L2Ball, intersect_constraints
from fedact.certification.uncertainty import solve_action_interval
from fedact.data.synthetic import effective_support
from fedact.domain.types import (
    ActionCount,
    ClientIdentifier,
    ClientIndex,
    EffectiveSampleSize,
    IntervalBound,
    LogDeterminantGain,
    MetricRate,
    Probability,
    RidgeLambda,
    SampleCount,
    SeedValue,
    SelectedCount,
)

FloatArray = NDArray[np.float64]
_BALL_DIAMETER_DOUBLING_FACTOR = 2.0


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
    current_sum: FloatArray, candidate: FloatArray, ridge_lambda: RidgeLambda
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


@dataclass(frozen=True)
class ClientInformationMatrix:
    client: ClientIdentifier
    matrix: FloatArray


def greedy_d_optimal(
    information_matrices: tuple[ClientInformationMatrix, ...],
    ridge_lambda: RidgeLambda,
    budget: SelectionBudget,
) -> tuple[ClientIdentifier, ...]:
    by_client = {entry.client: entry.matrix for entry in information_matrices}
    selected: list[ClientIdentifier] = []
    remaining = sorted(by_client)
    dimension = next(iter(by_client.values())).shape[0]
    accumulated: FloatArray = np.zeros((dimension, dimension))
    while len(selected) < budget.selected_count and remaining:
        gains = {
            client: d_optimal_gain(accumulated, by_client[client], ridge_lambda)
            for client in remaining
        }
        best = min(gains.items(), key=lambda item: (-item[1], item[0]))[0]
        selected.append(best)
        remaining.remove(best)
        accumulated = accumulated + by_client[best]
    return tuple(selected)


def uniform_action_weights(action_count: ActionCount) -> tuple[Probability, ...]:
    if action_count == 0:
        return ()
    weight = 1.0 / action_count
    return tuple(weight for _unused in range(action_count))


def random_selection(
    clients: tuple[ClientIdentifier, ...],
    seed: SeedValue,
    budget: SelectionBudget,
) -> tuple[ClientIdentifier, ...]:
    rng = np.random.default_rng(seed)
    ordered = sorted(clients)
    chosen = rng.choice(len(ordered), size=budget.selected_count, replace=False)
    return tuple(sorted(ordered[int(index)] for index in chosen.tolist()))


@dataclass(frozen=True)
class MaliciousSupportCount:
    client: ClientIdentifier
    historical_malicious_count: SampleCount
    later_malicious_count: SampleCount

    @property
    def effective_support(self) -> EffectiveSampleSize | None:
        if self.historical_malicious_count <= 0 or self.later_malicious_count <= 0:
            return None
        return effective_support(self.historical_malicious_count, self.later_malicious_count)


def largest_sample_count_selection(
    supports: tuple[MaliciousSupportCount, ...],
    budget: SelectionBudget,
) -> tuple[ClientIdentifier, ...]:
    ranked = sorted(
        supports,
        key=lambda support: (
            -(support.effective_support if support.effective_support is not None else -1.0),
            support.client,
        ),
    )
    return tuple(support.client for support in ranked[: budget.selected_count])


def ball_support_width(ball: L2Ball, direction: torch.Tensor) -> IntervalBound:
    norm_direction = float(np.linalg.norm(direction.detach().cpu().numpy()))
    return _BALL_DIAMETER_DOUBLING_FACTOR * ball.radius * norm_direction


def weighted_action_width(
    action_directions: tuple[torch.Tensor, ...],
    action_weights: tuple[Probability, ...],
    plausibility_ball: L2Ball,
    selected_constraints: tuple[ClientConstraint, ...],
    vertices: SampleCount,
) -> IntervalBound:
    if not selected_constraints:
        return sum(
            weight * ball_support_width(plausibility_ball, direction)
            for direction, weight in zip(action_directions, action_weights, strict=True)
        )
    feasible_set = intersect_constraints(plausibility_ball, selected_constraints, vertices=vertices)
    return sum(
        weight * solve_action_interval(direction, feasible_set).width
        for direction, weight in zip(action_directions, action_weights, strict=True)
    )


def greedy_action_interval_contraction_selection(
    action_directions: tuple[torch.Tensor, ...],
    action_weights: tuple[Probability, ...],
    constraints: tuple[ClientConstraint, ...],
    plausibility_ball: L2Ball,
    budget: SelectionBudget,
    vertices: SampleCount,
) -> tuple[ClientIndex, ...]:
    by_client = {constraint.client_index: constraint for constraint in constraints}
    remaining = sorted(by_client)
    selected: list[ClientIndex] = []
    current_width = weighted_action_width(
        action_directions, action_weights, plausibility_ball, (), vertices
    )
    while len(selected) < budget.selected_count and remaining:
        gains: dict[ClientIndex, IntervalBound] = {}
        for client in remaining:
            candidate = tuple(by_client[identifier] for identifier in (*selected, client))
            candidate_width = weighted_action_width(
                action_directions, action_weights, plausibility_ball, candidate, vertices
            )
            gains[client] = current_width - candidate_width
        best = max(gains.items(), key=lambda item: (item[1], item[0]))[0]
        selected.append(best)
        remaining.remove(best)
        current_width = weighted_action_width(
            action_directions,
            action_weights,
            plausibility_ball,
            tuple(by_client[identifier] for identifier in selected),
            vertices,
        )
    return tuple(selected)
