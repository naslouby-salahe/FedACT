from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

from fedact.calibration.nested import CalibrationCandidate
from fedact.domain.records import RankDimension

CoverageThreshold = Annotated[float, Field(ge=0.0, le=1.0)]
DegradationBound = Annotated[float, Field(ge=0.0)]


class CalibrationSelectionError(ValueError):
    pass


@dataclass(frozen=True)
class SelectedCalibration:
    selected_candidate: CalibrationCandidate
    selection_rank: RankDimension


def select_best_calibration_candidate(
    candidates: tuple[CalibrationCandidate, ...],
    target_coverage: CoverageThreshold,
    max_clean_degradation: DegradationBound,
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
