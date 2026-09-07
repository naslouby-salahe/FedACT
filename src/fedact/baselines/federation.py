from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


class FederationComparatorName(StrEnum):
    CENTRALIZED_POOLED = "centralized_pooled"
    LOCAL_ONLY = "local_only"


@dataclass(frozen=True)
class FederationConditionResult:
    aggregate_shift: FloatArray
    condition_name: FederationComparatorName


def centralized_pooled_comparator(
    client_shifts: tuple[FloatArray, ...],
) -> FederationConditionResult:
    if not client_shifts:
        raise ValueError("pooled comparator requires client shifts")
    stacked = np.stack(client_shifts)
    return FederationConditionResult(
        aggregate_shift=stacked.mean(axis=0),
        condition_name=FederationComparatorName.CENTRALIZED_POOLED,
    )


def local_only_comparator(
    client_shift: FloatArray,
) -> FederationConditionResult:
    return FederationConditionResult(
        aggregate_shift=client_shift.copy(),
        condition_name=FederationComparatorName.LOCAL_ONLY,
    )
