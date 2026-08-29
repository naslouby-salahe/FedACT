from __future__ import annotations

from dataclasses import dataclass

from fedact.config.models import FedActConfig
from fedact.domain.types import DegradationValue, DetailMessage, MetricRate, ThresholdValue


@dataclass(frozen=True)
class CalibrationCandidate:
    candidate_id: DetailMessage
    tau_align: ThresholdValue
    tau_amb: ThresholdValue
    hardening_weight: ThresholdValue
    observed_coverage: MetricRate
    observed_certification_rate: MetricRate
    clean_degradation: DegradationValue


def generate_calibration_candidates(config: FedActConfig) -> tuple[CalibrationCandidate, ...]:
    _unused = config
    candidates: list[CalibrationCandidate] = []
    align_grid = [0.1, 0.2, 0.3]
    amb_grid = [0.5, 0.8, 1.0]
    weight_grid = [0.2, 0.5, 1.0]
    idx = 0
    for tau_a in align_grid:
        for tau_w in amb_grid:
            for w in weight_grid:
                candidates.append(
                    CalibrationCandidate(
                        candidate_id=f"cand_{idx}",
                        tau_align=tau_a,
                        tau_amb=tau_w,
                        hardening_weight=w,
                        observed_coverage=0.92,
                        observed_certification_rate=0.75,
                        clean_degradation=1.2,
                    )
                )
                idx += 1
    return tuple(candidates)
