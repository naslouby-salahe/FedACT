from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from fedact.domain.types import MetricRate, ProbabilityValue, ThresholdValue


@dataclass(frozen=True)
class EquivalenceTestResult:
    t_lower: ThresholdValue
    t_upper: ThresholdValue
    p_value: ProbabilityValue
    is_equivalent: bool


def tost_equivalence(
    treatment: Sequence[MetricRate],
    control: Sequence[MetricRate],
    equivalence_margin: ThresholdValue = 0.05,
    alpha: ProbabilityValue = 0.05,
) -> EquivalenceTestResult:
    if len(treatment) != len(control) or len(treatment) < 2:
        return EquivalenceTestResult(t_lower=0.0, t_upper=0.0, p_value=1.0, is_equivalent=False)
    diffs = [float(t - c) for t, c in zip(treatment, control, strict=True)]
    n = len(diffs)
    mean_d = sum(diffs) / n
    variance_d = sum((d - mean_d) ** 2 for d in diffs) / (n - 1)
    std_err = math.sqrt(variance_d / n) if variance_d > 1e-12 else 1e-12

    t_lower = (mean_d - (-equivalence_margin)) / std_err
    t_upper = (mean_d - equivalence_margin) / std_err

    p_lower = math.erfc(t_lower / math.sqrt(2.0)) / 2.0
    p_upper = math.erfc(-t_upper / math.sqrt(2.0)) / 2.0
    p_val = max(p_lower, p_upper)
    p_val = max(0.0, min(1.0, float(p_val)))

    return EquivalenceTestResult(
        t_lower=float(t_lower),
        t_upper=float(t_upper),
        p_value=p_val,
        is_equivalent=bool(p_val < alpha),
    )
