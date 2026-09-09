from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fedact.domain.types import (
    CutoffCount,
    CutoffDifferenceValue,
    EffectDirection,
    MetricRate,
    MissingCutoffReason,
    PairedCutoffCount,
    ParameterName,
    SeedValue,
    SplitCutoffIdentity,
    SufficiencyFlag,
    ThresholdValue,
)


@dataclass(frozen=True)
class SeedLevelEndpointObservation:
    cutoff_identity: SplitCutoffIdentity
    seed_index: SeedValue
    value: ThresholdValue | None
    missing_reason: MissingCutoffReason | None


@dataclass(frozen=True)
class CutoffAggregate:
    cutoff_identity: SplitCutoffIdentity
    value: ThresholdValue | None
    missing_reason: MissingCutoffReason | None


def aggregate_cutoff_from_seeds(
    observations: tuple[SeedLevelEndpointObservation, ...],
) -> CutoffAggregate:
    if not observations:
        raise ValueError("cutoff aggregation requires at least one seed-level observation")
    cutoff_identity = observations[0].cutoff_identity
    finite_values = tuple(
        observation.value for observation in observations if observation.value is not None
    )
    if not finite_values:
        reason = next(
            (
                observation.missing_reason
                for observation in observations
                if observation.missing_reason is not None
            ),
            MissingCutoffReason.MISSING_SOURCE_DATA,
        )
        return CutoffAggregate(cutoff_identity=cutoff_identity, value=None, missing_reason=reason)
    return CutoffAggregate(
        cutoff_identity=cutoff_identity,
        value=sum(finite_values) / len(finite_values),
        missing_reason=None,
    )


@dataclass(frozen=True)
class PairedContrastInputs:
    paired_differences: tuple[CutoffDifferenceValue, ...]
    eligible_cutoff_count: CutoffCount
    missing_cutoff_count: CutoffCount
    sufficient: SufficiencyFlag


def build_paired_contrast(
    method_a: tuple[CutoffAggregate, ...],
    method_b: tuple[CutoffAggregate, ...],
    minimum_paired_cutoffs: PairedCutoffCount,
    maximum_missing_cutoff_fraction: MetricRate,
) -> PairedContrastInputs:
    aggregates_by_cutoff_a = {aggregate.cutoff_identity: aggregate for aggregate in method_a}
    aggregates_by_cutoff_b = {aggregate.cutoff_identity: aggregate for aggregate in method_b}
    eligible_cutoffs = sorted(set(aggregates_by_cutoff_a) & set(aggregates_by_cutoff_b))
    differences: list[CutoffDifferenceValue] = []
    missing_count = 0
    for cutoff_identity in eligible_cutoffs:
        aggregate_a = aggregates_by_cutoff_a[cutoff_identity]
        aggregate_b = aggregates_by_cutoff_b[cutoff_identity]
        if aggregate_a.value is None or aggregate_b.value is None:
            missing_count += 1
            continue
        differences.append(aggregate_a.value - aggregate_b.value)
    eligible_count = len(eligible_cutoffs)
    missing_fraction = missing_count / eligible_count if eligible_count > 0 else 1.0
    sufficient = (
        len(differences) >= minimum_paired_cutoffs
        and missing_fraction <= maximum_missing_cutoff_fraction
    )
    return PairedContrastInputs(
        paired_differences=tuple(differences),
        eligible_cutoff_count=eligible_count,
        missing_cutoff_count=missing_count,
        sufficient=sufficient,
    )


def contrast_effect_direction(
    paired_differences: tuple[CutoffDifferenceValue, ...],
) -> EffectDirection:
    positive = sum(1 for difference in paired_differences if difference > 0.0)
    negative = sum(1 for difference in paired_differences if difference < 0.0)
    if positive > negative:
        return EffectDirection.FAVORABLE
    if negative > positive:
        return EffectDirection.CONTRADICTORY
    return EffectDirection.NEUTRAL


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
