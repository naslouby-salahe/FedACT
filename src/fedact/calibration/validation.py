from __future__ import annotations

from fedact.calibration.selection import SelectedCalibration


class CalibrationValidationError(ValueError):
    pass


def validate_calibration_outcome(selected: SelectedCalibration) -> None:
    if selected.selected_candidate.observed_coverage < 0.8:
        raise CalibrationValidationError(
            "selected candidate coverage below empirical validity limit"
        )
