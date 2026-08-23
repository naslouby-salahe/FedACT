from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import numpy as np
from numpy.typing import NDArray
from pydantic import Field

FloatArray = NDArray[np.float64]
SpaceDimension = Annotated[int, Field(ge=1)]
SeedIdentifier = Annotated[int, Field(ge=0)]


@dataclass(frozen=True)
class SecurityComparatorResult:
    predicted_shift: FloatArray
    comparator_family: str


def static_security_baseline(dimension: SpaceDimension = 64) -> SecurityComparatorResult:
    return SecurityComparatorResult(
        predicted_shift=np.zeros(dimension),
        comparator_family="static",
    )


def random_mutation_baseline(
    dimension: SpaceDimension = 64, seed: SeedIdentifier = 2026
) -> SecurityComparatorResult:
    rng = np.random.default_rng(seed)
    shift = rng.standard_normal(dimension)
    shift /= np.linalg.norm(shift)
    return SecurityComparatorResult(
        predicted_shift=shift,
        comparator_family="random_mutation",
    )


def reactive_adaptation_baseline(
    observed_recent_shift: FloatArray,
) -> SecurityComparatorResult:
    return SecurityComparatorResult(
        predicted_shift=observed_recent_shift.copy(),
        comparator_family="reactive",
    )
