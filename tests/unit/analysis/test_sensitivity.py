from __future__ import annotations

from fedact.analysis.sensitivity import SensitivityAxis, enumerate_sensitivity_coordinates


def test_enumerate_sensitivity_coordinates_covers_locked_axes() -> None:
    coordinates = enumerate_sensitivity_coordinates(
        control_span_alphas=(0.01, 0.05),
        private_contamination_alphas=(0.01,),
        radius_multipliers=(1.0, 1.5),
        alignment_percentiles=(90.0,),
        ambiguity_percentiles=(80.0,),
        forecast_horizons=(1.0, 3.0),
        nuisance_ranks=(2.0, 4.0),
        coverage_levels=(0.9,),
    )
    axes = {coordinate.axis for coordinate in coordinates}
    assert SensitivityAxis.CONTROL_SPAN_VIOLATION in axes
    assert SensitivityAxis.TARGET_COVERAGE in axes
    assert len(coordinates) == 12
