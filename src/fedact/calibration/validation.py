from __future__ import annotations

from fedact.calibration.selection import CoverageThreshold, SelectedCalibration


class CalibrationValidationError(ValueError):
    pass


def validate_calibration_outcome(
    selected: SelectedCalibration, minimum_coverage: CoverageThreshold
) -> None:
    if selected.selected_candidate.observed_coverage < minimum_coverage:
        raise CalibrationValidationError(
            "selected candidate coverage below empirical validity limit"
        )
