from __future__ import annotations

from dataclasses import dataclass

from fedact.domain.types import (
    CoverageLevel,
    DegradationValue,
    DetailMessage,
    MetricRate,
    RankDimension,
    ThresholdValue,
)


@dataclass(frozen=True)
class CalibrationCandidate:
    candidate_id: DetailMessage
    tau_align: ThresholdValue
    tau_amb: ThresholdValue
    hardening_weight: ThresholdValue
    observed_coverage: MetricRate
    observed_certification_rate: MetricRate
    clean_degradation: DegradationValue


class CalibrationSelectionError(ValueError):
    pass


@dataclass(frozen=True)
class SelectedCalibration:
    selected_candidate: CalibrationCandidate
    selection_rank: RankDimension


def select_best_calibration_candidate(
    candidates: tuple[CalibrationCandidate, ...],
    target_coverage: CoverageLevel,
    max_clean_degradation: DegradationValue,
) -> SelectedCalibration:
    valid = [
        c
        for c in candidates
        if c.observed_coverage >= target_coverage and c.clean_degradation <= max_clean_degradation
    ]
    if not valid:
        raise CalibrationSelectionError(
            "no calibration candidate satisfies coverage and clean cost gates"
        )
    sorted_candidates = sorted(
        valid,
        key=lambda c: (-c.observed_certification_rate, c.clean_degradation, c.candidate_id),
    )
    return SelectedCalibration(
        selected_candidate=sorted_candidates[0],
        selection_rank=1,
    )


class CalibrationValidationError(ValueError):
    pass


def validate_calibration_outcome(
    selected: SelectedCalibration, minimum_coverage: CoverageLevel
) -> None:
    if selected.selected_candidate.observed_coverage < minimum_coverage:
        raise CalibrationValidationError(
            "selected candidate coverage below empirical validity limit"
        )
