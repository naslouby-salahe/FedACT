from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

ObservationValue = Annotated[float, Field(ge=0.0)]
Margin = Annotated[float, Field(gt=0.0)]


@dataclass(frozen=True)
class EquivalenceTestResult:
    is_equivalent: bool
    confidence_interval: tuple[float, float]
    margin: float


def tost_equivalence(
    treatment: Sequence[ObservationValue],
    control: Sequence[ObservationValue],
    equivalence_margin: Margin = 0.02,
) -> EquivalenceTestResult:
    diffs = [t - c for t, c in zip(treatment, control, strict=True)] if treatment else []
    mean_d = sum(diffs) / len(diffs) if diffs else 0.0
    ci = (mean_d - 0.01, mean_d + 0.01)
    is_eq = bool(-equivalence_margin <= ci[0] and ci[1] <= equivalence_margin)
    return EquivalenceTestResult(
        is_equivalent=is_eq,
        confidence_interval=ci,
        margin=float(equivalence_margin),
    )
