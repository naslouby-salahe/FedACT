from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fedact.domain.records import MetricRate, ParameterName, ThresholdValue


class SensitivityAxis(StrEnum):
    CONTROL_SPAN_VIOLATION = "control_span_violation"
    PRIVATE_CONTAMINATION = "private_contamination"
    HISTORICAL_PLAUSIBILITY_RADIUS = "historical_plausibility_radius"
    ALIGNMENT_THRESHOLD = "alignment_threshold"
    AMBIGUITY_WIDTH = "ambiguity_width"
    FORECAST_HORIZON = "forecast_horizon"
    NUISANCE_RANK = "nuisance_rank"
    TARGET_COVERAGE = "target_coverage"


@dataclass(frozen=True)
class SensitivityCoordinate:
    axis: SensitivityAxis
    parameter_name: ParameterName
    value: ThresholdValue


@dataclass(frozen=True)
class SensitivityOutcome:
    coordinate: SensitivityCoordinate
    effect_estimate: MetricRate
    certification_rate: MetricRate
    abstention_rate: MetricRate
    clean_cost: MetricRate


def enumerate_sensitivity_coordinates(
    control_span_alphas: tuple[ThresholdValue, ...],
    private_contamination_alphas: tuple[ThresholdValue, ...],
    radius_multipliers: tuple[ThresholdValue, ...],
    alignment_percentiles: tuple[ThresholdValue, ...],
    ambiguity_percentiles: tuple[ThresholdValue, ...],
    forecast_horizons: tuple[ThresholdValue, ...],
    nuisance_ranks: tuple[ThresholdValue, ...],
    coverage_levels: tuple[ThresholdValue, ...],
) -> tuple[SensitivityCoordinate, ...]:
    axes = (
        (SensitivityAxis.CONTROL_SPAN_VIOLATION, "rho", control_span_alphas),
        (SensitivityAxis.PRIVATE_CONTAMINATION, "xi", private_contamination_alphas),
        (SensitivityAxis.HISTORICAL_PLAUSIBILITY_RADIUS, "R", radius_multipliers),
        (SensitivityAxis.ALIGNMENT_THRESHOLD, "tau_align", alignment_percentiles),
        (SensitivityAxis.AMBIGUITY_WIDTH, "tau_amb", ambiguity_percentiles),
        (SensitivityAxis.FORECAST_HORIZON, "horizon", forecast_horizons),
        (SensitivityAxis.NUISANCE_RANK, "nuisance_rank", nuisance_ranks),
        (SensitivityAxis.TARGET_COVERAGE, "coverage_level", coverage_levels),
    )
    return tuple(
        SensitivityCoordinate(axis=axis, parameter_name=parameter_name, value=value)
        for axis, parameter_name, values in axes
        for value in values
    )
