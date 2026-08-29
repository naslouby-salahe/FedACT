from __future__ import annotations

from collections.abc import Sequence

from fedact.domain.types import ProbabilityValue


def benjamini_hochberg_correction(
    p_values: Sequence[ProbabilityValue],
    false_discovery_rate: ProbabilityValue = 0.05,
) -> tuple[ProbabilityValue, ...]:
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
