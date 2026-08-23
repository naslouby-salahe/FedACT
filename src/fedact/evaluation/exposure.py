from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated

from pydantic import Field

LossValue = Annotated[float, Field(ge=0.0)]
CumulativeLoss = Annotated[float, Field(ge=0.0)]
LossThreshold = Annotated[float, Field(ge=0.0)]
CatchUpStep = Annotated[int, Field(ge=0)]


def compute_cumulative_exposure(losses: Sequence[LossValue]) -> CumulativeLoss:
    return float(sum(losses))


def compute_time_to_catch_up(
    baseline_losses: Sequence[LossValue],
    hardened_losses: Sequence[LossValue],
    threshold: LossThreshold = 0.05,
) -> CatchUpStep | None:
    for t, (b, h) in enumerate(zip(baseline_losses, hardened_losses, strict=True)):
        if abs(h - b) <= threshold:
            return t
    return None
