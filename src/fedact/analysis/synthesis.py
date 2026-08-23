from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

from fedact.domain.types import MetricRate, ThresholdValue


@dataclass(frozen=True)
class TreatmentEffectSynthesis:
    pooled_mean_diff: ThresholdValue
    pooled_variance: ThresholdValue
    cohens_d: ThresholdValue


def synthesize_treatment_effects(
    treatment: Sequence[MetricRate],
    control: Sequence[MetricRate],
) -> TreatmentEffectSynthesis:
    if not treatment or not control:
        return TreatmentEffectSynthesis(pooled_mean_diff=0.0, pooled_variance=0.0, cohens_d=0.0)
    n1, n2 = len(treatment), len(control)
    m1 = sum(treatment) / n1
    m2 = sum(control) / n2
    diff = m1 - m2

    var1 = sum((x - m1) ** 2 for x in treatment) / max(1, n1 - 1)
    var2 = sum((x - m2) ** 2 for x in control) / max(1, n2 - 1)

    if n1 + n2 > 2:
        pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    else:
        pooled_var = (var1 + var2) / 2.0

    s_pooled = math.sqrt(pooled_var) if pooled_var > 1e-12 else 1e-12
    cohens_d = diff / s_pooled

    return TreatmentEffectSynthesis(
        pooled_mean_diff=float(diff),
        pooled_variance=float(pooled_var),
        cohens_d=float(cohens_d),
    )
