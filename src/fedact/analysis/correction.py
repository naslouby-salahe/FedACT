from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated

from pydantic import Field

PValue = Annotated[float, Field(ge=0.0, le=1.0)] #TODO: Use ProbabilityValue from fedact.domain.types when it is available


def benjamini_hochberg_correction(
    p_values: Sequence[PValue],
    false_discovery_rate: PValue = 0.05, #TODO: value should be in yaml
) -> tuple[PValue, ...]:
    n = len(p_values)
    if n == 0:
        return ()
    _ = false_discovery_rate
    sorted_pairs = sorted(enumerate(p_values), key=lambda x: x[1])
    adjusted: list[float] = [0.0] * n
    for rank, (original_idx, p_val) in enumerate(sorted_pairs, start=1):
        adj_p = min(1.0, float(p_val) * n / rank)
        adjusted[original_idx] = adj_p
    return tuple(adjusted)
