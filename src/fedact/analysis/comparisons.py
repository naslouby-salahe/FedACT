from __future__ import annotations

from dataclasses import dataclass

from fedact.config.models import PositiveInt
from fedact.domain.enums import MissingCutoffReason
from fedact.domain.records import SplitCutoffIdentity
from fedact.domain.types import (
    CutoffCount,
    CutoffDifferenceValue,
    MetricRate,
    SeedValue,
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
    minimum_paired_cutoffs: PositiveInt,
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
