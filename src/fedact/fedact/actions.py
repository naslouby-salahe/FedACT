from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import numpy as np
from numpy.typing import NDArray
from pydantic import Field

from fedact.fedact.estimand import ActionInterval

FloatArray = NDArray[np.float64]
ZeroDisplacementFloor = Annotated[float, Field(gt=0.0)]
DiameterBound = Annotated[float, Field(ge=0.0)]


@dataclass(frozen=True)
class ActionDisplacementResult:
    direction: FloatArray
    displacement_norm: float
    rejected_as_degenerate: bool


def evaluate_displacement(
    original_embedding: FloatArray,
    transformed_embedding: FloatArray,
    zero_displacement_floor: ZeroDisplacementFloor,
) -> ActionDisplacementResult:
    difference = transformed_embedding - original_embedding
    norm = float(np.linalg.norm(difference))
    if norm < zero_displacement_floor:
        return ActionDisplacementResult(
            direction=np.zeros_like(difference),
            displacement_norm=norm,
            rejected_as_degenerate=True,
        )
    return ActionDisplacementResult(
        direction=difference / norm,
        displacement_norm=norm,
        rejected_as_degenerate=False,
    )


def action_support_bounds(
    direction: FloatArray, vertices: tuple[FloatArray, ...]
) -> ActionInterval:
    projections = [float(direction @ vertex) for vertex in vertices]
    return ActionInterval(lower=min(projections), upper=max(projections))


def box_diameter_bound(
    lower_bounds: tuple[float, ...], upper_bounds: tuple[float, ...]
) -> DiameterBound:
    squared = sum(
        (upper - lower) ** 2 for lower, upper in zip(lower_bounds, upper_bounds, strict=True)
    )
    value: DiameterBound = float(squared**0.5)
    return value
