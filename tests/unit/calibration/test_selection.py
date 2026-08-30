from __future__ import annotations

from fedact.calibration.nested import CalibrationCandidate
from fedact.calibration.selection import select_best_calibration_candidate


def test_select_best_calibration_candidate() -> None:
    c1 = CalibrationCandidate(
        candidate_id="c1",
        tau_align=0.2,
        tau_amb=0.8,
        hardening_weight=0.5,
        observed_coverage=0.95,
        observed_certification_rate=0.80,
        clean_degradation=1.0,
    )
    c2 = CalibrationCandidate(
        candidate_id="c2",
        tau_align=0.2,
        tau_amb=0.8,
        hardening_weight=0.5,
        observed_coverage=0.95,
        observed_certification_rate=0.60,
        clean_degradation=1.0,
    )
    selected = select_best_calibration_candidate(
        (c1, c2), target_coverage=0.90, max_clean_degradation=2.0
    )
    assert selected.selected_candidate.candidate_id == "c1"
