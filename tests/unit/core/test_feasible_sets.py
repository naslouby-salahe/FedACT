from __future__ import annotations

import numpy as np

from fedact.core.feasible_sets import (
    ClientConstraint,
    L2Ball,
    intersect_constraints,
    minimum_uniform_inflation,
)


def test_historical_plausibility_ball_contains_center() -> None:
    ball = L2Ball(center=np.zeros(4), radius=2.0)
    assert ball.is_containing(np.zeros(4), tolerance=1e-6)
    assert not ball.is_containing(np.ones(4) * 3.0, tolerance=1e-6)


def test_intersect_constraints_combines_multiple_balls() -> None:
    c1 = ClientConstraint(
        projector=np.eye(2),
        covariance=np.eye(2),
        beta=1.5,
        client_index=0,
    )
    feas = intersect_constraints(L2Ball(center=np.zeros(2), radius=1.0), (c1,), vertices=512)
    assert feas is not None


def test_minimum_uniform_inflation_for_disjoint_sets() -> None:
    c1 = ClientConstraint(
        projector=np.eye(2),
        covariance=np.eye(2),
        beta=0.1,
        client_index=0,
    )
    inflation = minimum_uniform_inflation(
        L2Ball(center=np.zeros(2), radius=1.0), (c1,), vertices=100
    )
    assert inflation >= 1.0
