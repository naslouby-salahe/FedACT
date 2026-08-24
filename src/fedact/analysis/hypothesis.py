from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from fedact.domain.types import MetricRate, ProbabilityValue, ThresholdValue


@dataclass(frozen=True)
class HypothesisTestResult:
    test_statistic: ThresholdValue
    p_value: ProbabilityValue
    is_significant: bool


def paired_t_test(
    treatment: Sequence[MetricRate],
    control: Sequence[MetricRate],
    alpha: ProbabilityValue = 0.05, #TODO: this value should be in yaml
) -> HypothesisTestResult:
    if len(treatment) != len(control) or len(treatment) < 2:
        return HypothesisTestResult(test_statistic=0.0, p_value=1.0, is_significant=False)
    diffs = [float(t - c) for t, c in zip(treatment, control, strict=True)]
    n = len(diffs)
    mean_d = sum(diffs) / n
    variance_d = sum((d - mean_d) ** 2 for d in diffs) / (n - 1)
    std_err = math.sqrt(variance_d / n) if variance_d > 1e-12 else 0.0

    if std_err > 1e-12:
        t_stat = mean_d / std_err
        z = abs(t_stat)
        p_val = math.erfc(z / math.sqrt(2.0))
    elif abs(mean_d) > 1e-12:
        t_stat = -100.0 if mean_d < 0 else 100.0
        p_val = 0.0001
    else:
        t_stat = 0.0
        p_val = 1.0

    p_val = max(0.0, min(1.0, float(p_val)))
    return HypothesisTestResult(
        test_statistic=float(t_stat),
        p_value=p_val,
        is_significant=bool(p_val < alpha),
    )
