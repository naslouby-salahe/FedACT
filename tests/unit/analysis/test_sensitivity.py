from __future__ import annotations

from fedact.analysis.comparisons import SensitivityAxis, enumerate_sensitivity_coordinates
from fedact.domain.types import SensitivityParameterName


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


AXIS_TO_PARAMETER_MEMBER = {"CONTROL_SPAN_VIOLATION": "CONTROL_SPAN"}


def _parameter_member_for(axis_member: str) -> str:
    return AXIS_TO_PARAMETER_MEMBER.get(axis_member, axis_member)


def test_sensitivity_axis_and_parameter_name_vocabularies_stay_in_correspondence() -> None:
    axis_members = {member.name for member in SensitivityAxis}
    parameter_members = {member.name for member in SensitivityParameterName}
    assert len(axis_members) == len(parameter_members)
    assert {_parameter_member_for(name) for name in axis_members} == parameter_members


def test_every_sensitivity_axis_pairs_with_exactly_one_parameter_name() -> None:
    coordinates = enumerate_sensitivity_coordinates(
        control_span_alphas=(0.05,),
        private_contamination_alphas=(0.05,),
        radius_multipliers=(1.0,),
        alignment_percentiles=(90.0,),
        ambiguity_percentiles=(80.0,),
        forecast_horizons=(3.0,),
        nuisance_ranks=(4.0,),
        coverage_levels=(0.9,),
    )
    pairs = [(coordinate.axis, coordinate.parameter_name) for coordinate in coordinates]
    assert len(pairs) == len(set(pairs)) == len(SensitivityAxis)
    assert {axis for axis, _unused in pairs} == set(SensitivityAxis)
    assert {name for _unused, name in pairs} == set(SensitivityParameterName)
