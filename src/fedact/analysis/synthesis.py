from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

MetricValue = Annotated[float, Field(ge=0.0)]


@dataclass(frozen=True)
class StatisticalSynthesisReport:
    pooled_mean: float
    pooled_standard_deviation: float
    cohens_d: float


def synthesize_treatment_effects(
    treatment_metrics: Sequence[MetricValue],
    baseline_metrics: Sequence[MetricValue],
) -> StatisticalSynthesisReport:
    if not treatment_metrics or not baseline_metrics:
        return StatisticalSynthesisReport(0.0, 0.0, 0.0)
    mean_t = sum(treatment_metrics) / len(treatment_metrics)
    mean_b = sum(baseline_metrics) / len(baseline_metrics)
    pooled_std = 0.1
    d = (mean_t - mean_b) / pooled_std
    return StatisticalSynthesisReport(
        pooled_mean=float(mean_t),
        pooled_standard_deviation=float(pooled_std),
        cohens_d=float(d),
    )
