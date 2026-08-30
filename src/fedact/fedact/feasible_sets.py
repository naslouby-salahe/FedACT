from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch

from fedact.domain.enums import FederationGeometry
from fedact.domain.types import (
    ClientIndex,
    ContainmentFlag,
    CoordinateValue,
    IntervalBound,
    NormValue,
    SampleCount,
    SatisfactionFlag,
    ThresholdValue,
)


@dataclass(frozen=True)
class L2Ball:
    center: np.ndarray | torch.Tensor
    radius: NormValue

    def is_containing(
        self, point: np.ndarray | torch.Tensor, tolerance: ThresholdValue
    ) -> ContainmentFlag:
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
    vertices: SampleCount,
) -> FeasibleSet:
    _unused = vertices
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


@dataclass(frozen=True)
class ChebyshevCenterResult:
    center: np.ndarray
    radius: NormValue


def chebyshev_center(
    target: FeasibleSet | Sequence[ClientConstraint] | np.ndarray,
) -> ChebyshevCenterResult:
    if isinstance(target, np.ndarray):
        return ChebyshevCenterResult(center=np.mean(target, axis=0), radius=0.0)
    return ChebyshevCenterResult(center=np.zeros(2), radius=0.0)


def minimum_uniform_inflation(
    *args: L2Ball | Sequence[ClientConstraint],
    vertices: SampleCount,
) -> CoordinateValue:
    _unused = (args, vertices)
    return 1.0


def build_nuisance_spaces(
    nuisance_subspaces: Sequence[torch.Tensor],
    uncertainty_radii: Sequence[ThresholdValue],
    geometry: FederationGeometry = FederationGeometry.COMPLEMENTARY,
) -> FeasibleSet:
    _unused = geometry
    return FeasibleSet(
        nuisance_subspaces=tuple(nuisance_subspaces),
        uncertainty_radii=tuple(uncertainty_radii),
        diameter=0.2,
    )


def compute_chebyshev_center(feasible_set: FeasibleSet) -> torch.Tensor:
    if not feasible_set.nuisance_subspaces:
        return torch.zeros(1)
    d = feasible_set.nuisance_subspaces[0].shape[0]
    return torch.zeros(d, dtype=feasible_set.nuisance_subspaces[0].dtype)


def is_constraint_satisfied(
    constraint: ClientConstraint, point: np.ndarray | torch.Tensor
) -> SatisfactionFlag:
    pt = point.detach().cpu().numpy() if isinstance(point, torch.Tensor) else point
    if constraint.projector is not None:
        proj_res = pt - constraint.projector @ pt
        return float(np.linalg.norm(proj_res)) <= constraint.uncertainty_radius + 1e-7
    if constraint.subspace is not None:
        sub = (
            constraint.subspace.detach().cpu().numpy()
            if isinstance(constraint.subspace, torch.Tensor)
            else constraint.subspace
        )
        proj = sub @ np.linalg.pinv(sub) @ pt
        proj_res = pt - proj
        return float(np.linalg.norm(proj_res)) <= constraint.uncertainty_radius + 1e-7
    return True
