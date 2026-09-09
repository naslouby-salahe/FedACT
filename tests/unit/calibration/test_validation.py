from __future__ import annotations

from fedact.certification.calibration import (
    CalibrationCandidate,
    SelectedCalibration,
    validate_calibration_outcome,
)


def test_validate_calibration_outcome() -> None:
    cand = CalibrationCandidate(
        candidate_id="c1",
        tau_align=0.2,
        tau_amb=0.8,
        hardening_weight=0.5,
        observed_coverage=0.95,
        observed_certification_rate=0.80,
        clean_degradation=1.0,
    )
    selected = SelectedCalibration(selected_candidate=cand, selection_rank=1)
    validate_calibration_outcome(selected, minimum_coverage=0.8)
