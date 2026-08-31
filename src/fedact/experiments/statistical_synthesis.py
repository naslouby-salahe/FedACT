from __future__ import annotations

from dataclasses import dataclass

from fedact.analysis.sensitivity import (
    SensitivityAxis,
    SensitivityCoordinate,
    enumerate_sensitivity_coordinates,
)
from fedact.domain.enums import ScientificOutcome
from fedact.domain.records import DegradationValue, MetricRate, ValidationFlag


@dataclass(frozen=True)
class StatisticalSynthesisReport:
    coverage_satisfied: ValidationFlag
    clean_cost_satisfied: ValidationFlag
    overall_scientific_outcome: ScientificOutcome
    sensitivity_coordinates: tuple[SensitivityCoordinate, ...]


def run_statistical_synthesis(
    prospective_fnr: MetricRate,
    clean_fnr_degradation: DegradationValue,
    coverage: MetricRate,
    maximum_coverage_deficit: MetricRate,
    maximum_clean_fnr_degradation: DegradationValue,
    control_span_alphas: tuple[MetricRate, ...],
    private_contamination_alphas: tuple[MetricRate, ...],
    radius_multipliers: tuple[MetricRate, ...],
    alignment_percentiles: tuple[MetricRate, ...],
    ambiguity_percentiles: tuple[MetricRate, ...],
    forecast_horizons: tuple[MetricRate, ...],
    nuisance_ranks: tuple[MetricRate, ...],
    coverage_levels: tuple[MetricRate, ...],
) -> StatisticalSynthesisReport:
    coverage_satisfied = coverage >= (1.0 - maximum_coverage_deficit)
    clean_cost_satisfied = clean_fnr_degradation <= maximum_clean_fnr_degradation
    outcome = (
        ScientificOutcome.PASS
        if coverage_satisfied and clean_cost_satisfied
        else ScientificOutcome.FAIL
    )
    coordinates = enumerate_sensitivity_coordinates(
        control_span_alphas=control_span_alphas,
        private_contamination_alphas=private_contamination_alphas,
        radius_multipliers=radius_multipliers,
        alignment_percentiles=alignment_percentiles,
        ambiguity_percentiles=ambiguity_percentiles,
        forecast_horizons=forecast_horizons,
        nuisance_ranks=nuisance_ranks,
        coverage_levels=coverage_levels,
    )
    if not any(coordinate.axis is SensitivityAxis.TARGET_COVERAGE for coordinate in coordinates):
        outcome = ScientificOutcome.INSUFFICIENT_EVIDENCE
    return StatisticalSynthesisReport(
        coverage_satisfied=coverage_satisfied,
        clean_cost_satisfied=clean_cost_satisfied,
        overall_scientific_outcome=outcome,
        sensitivity_coordinates=coordinates,
    )
