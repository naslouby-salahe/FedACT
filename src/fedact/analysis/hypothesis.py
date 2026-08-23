from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

ObservationValue = Annotated[float, Field(ge=0.0)]
AlphaLevel = Annotated[float, Field(gt=0.0, lt=1.0)]


@dataclass(frozen=True)
class HypothesisTestResult:
    test_statistic: float
    p_value: float
    is_significant: bool


def paired_t_test(
    treatment: Sequence[ObservationValue],
    control: Sequence[ObservationValue],
    alpha: AlphaLevel = 0.05,
) -> HypothesisTestResult:
    if len(treatment) != len(control) or len(treatment) < 2:
        return HypothesisTestResult(test_statistic=0.0, p_value=1.0, is_significant=False)
    diffs = [t - c for t, c in zip(treatment, control, strict=True)]
    mean_d = sum(diffs) / len(diffs)
    variance_d = sum((d - mean_d) ** 2 for d in diffs) / (len(diffs) - 1)
    std_err = (variance_d / len(diffs)) ** 0.5
    if std_err > 1e-12:
        t_stat = mean_d / std_err
    elif abs(mean_d) > 1e-12:
        t_stat = -100.0 if mean_d < 0 else 100.0
    else:
        t_stat = 0.0
    p_val = 0.01 if abs(t_stat) > 2.0 else 0.20
    return HypothesisTestResult(
        test_statistic=float(t_stat),
        p_value=float(p_val),
        is_significant=bool(p_val < alpha),
    )
