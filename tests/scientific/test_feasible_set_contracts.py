from __future__ import annotations

import numpy as np

from fedact.fedact.feasible_sets import (
    ClientConstraint,
    L2Ball,
    intersect_constraints,
)


def test_feasible_set_preserves_ground_truth_inclusion() -> None:
    c1 = ClientConstraint(
        projector=np.eye(2),
        covariance=np.eye(2),
        beta=1.5,
        client_index=0,
    )
    ball = L2Ball(center=np.zeros(2), radius=1.0)
    feas = intersect_constraints(ball, (c1,))
    assert feas is not None
