from __future__ import annotations

import numpy as np
import pytest

from fedact.core.client_selection import (
    ClientInformationMatrix,
    SelectionBudget,
    d_optimal_gain,
    greedy_d_optimal,
    uniform_action_weights,
)
from fedact.domain.records import ClientIdentifier


def test_uniform_action_weights() -> None:
    weights = uniform_action_weights(5)
    assert len(weights) == 5
    assert weights[0] == pytest.approx(0.2)


def test_d_optimal_gain_is_non_negative() -> None:
    current = np.eye(3) * 0.1
    h_k = np.diag([1.0, 0.0, 0.0])
    gain = d_optimal_gain(current, h_k, ridge_lambda=1e-6)
    assert gain > 0.0


def test_greedy_d_optimal_selects_budget_clients() -> None:
    h1 = np.diag([1.0, 0.0, 0.0])
    h2 = np.diag([0.0, 1.0, 0.0])
    h3 = np.diag([0.0, 0.0, 1.0])
    selected = greedy_d_optimal(
        information_matrices=(
            ClientInformationMatrix(client=ClientIdentifier("c1"), matrix=h1),
            ClientInformationMatrix(client=ClientIdentifier("c2"), matrix=h2),
            ClientInformationMatrix(client=ClientIdentifier("c3"), matrix=h3),
        ),
        ridge_lambda=1e-6,
        budget=SelectionBudget(budget_fraction=0.5, eligible_clients=3),
    )
    assert len(selected) == 2
