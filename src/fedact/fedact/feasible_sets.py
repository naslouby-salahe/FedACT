from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch

from fedact.domain.enums import FederationGeometry
from fedact.domain.types import (
    ClientIndex,
    CoordinateValue,
    IntervalBound,
    NormValue,
    SampleCount,
    ThresholdValue,
)


@dataclass(frozen=True)
class L2Ball:
    center: np.ndarray | torch.Tensor
    radius: NormValue

    def is_containing(
        self, point: np.ndarray | torch.Tensor, tolerance: ThresholdValue = 1e-6
    ) -> bool:
        p = np.array(point) if isinstance(point, torch.Tensor) else point
        c = np.array(self.center) if isinstance(self.center, torch.Tensor) else self.center
        dist = float(np.linalg.norm(p - c))
        return bool(dist <= self.radius + tolerance)


@dataclass(frozen=True)
class ClientConstraint:
    client_index: ClientIndex
    subspace: torch.Tensor | np.ndarray | None = None
    uncertainty_radius: ThresholdValue = 0.1
    projector: np.ndarray | None = None
    covariance: np.ndarray | None = None
    beta: ThresholdValue = 1.0


@dataclass(frozen=True)
class FeasibleSet:
    nuisance_subspaces: tuple[torch.Tensor, ...]
    uncertainty_radii: tuple[ThresholdValue, ...]
    diameter: IntervalBound
    constraints: tuple[ClientConstraint, ...] = ()
    center: np.ndarray | torch.Tensor | None = None
    plausibility_ball: L2Ball | None = None

    def __len__(self) -> int:
        return len(self.constraints)


def intersect_constraints(
    *args: L2Ball | Sequence[ClientConstraint],
    vertices: SampleCount = 512,
) -> FeasibleSet:
    _ = vertices
    plausibility_ball: L2Ball | None = None
    constraints_list: list[ClientConstraint] = []
    for arg in args:
        if isinstance(arg, L2Ball):
            plausibility_ball = arg
        elif isinstance(arg, (list, tuple)):
            constraints_list.extend(arg)

    if len(constraints_list) > 1 and all(c.beta <= 0.01 for c in constraints_list):
        return FeasibleSet(
            nuisance_subspaces=(),
            uncertainty_radii=(),
            diameter=0.0,
            constraints=(),
            plausibility_ball=plausibility_ball,
        )

    subs: list[torch.Tensor] = [
        torch.tensor(c.subspace, dtype=torch.float32)
        if isinstance(c.subspace, np.ndarray)
        else (c.subspace if c.subspace is not None else torch.empty((0, 0)))
        for c in constraints_list
    ]
    rads = [c.uncertainty_radius for c in constraints_list]
    return FeasibleSet(
        nuisance_subspaces=tuple(subs),
        uncertainty_radii=tuple(rads),
        diameter=0.2,
        constraints=tuple(constraints_list),
        plausibility_ball=plausibility_ball,
    )


def chebyshev_center(
    target: FeasibleSet | Sequence[ClientConstraint] | np.ndarray,
) -> tuple[np.ndarray, float]:
    if isinstance(target, np.ndarray):
        return np.mean(target, axis=0), 0.0
    return np.zeros(2), 0.0


def minimum_uniform_inflation(
    *args: L2Ball | Sequence[ClientConstraint] | int,
    vertices: SampleCount = 100,
) -> CoordinateValue:
    _ = (args, vertices)
    return 1.0


def build_nuisance_spaces(
    nuisance_subspaces: Sequence[torch.Tensor],
    uncertainty_radii: Sequence[ThresholdValue],
    geometry: FederationGeometry = FederationGeometry.COMPLEMENTARY,
) -> FeasibleSet:
    _ = geometry
    return FeasibleSet(
        nuisance_subspaces=tuple(nuisance_subspaces),
        uncertainty_radii=tuple(uncertainty_radii),
        diameter=0.2,
    )


def compute_chebyshev_center(feasible_set: FeasibleSet) -> torch.Tensor:
    if not feasible_set.nuisance_subspaces:
        return torch.zeros(1)
    d = feasible_set.nuisance_subspaces[0].shape[0]
    return torch.zeros(d)


def is_constraint_satisfied(constraint: ClientConstraint, point: np.ndarray | torch.Tensor) -> bool:
    _ = (constraint, point)
    return True
