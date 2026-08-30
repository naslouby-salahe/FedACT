from __future__ import annotations

from fedact.analysis.comparisons import (
    CutoffAggregate,
    SeedLevelEndpointObservation,
    aggregate_cutoff_from_seeds,
    build_paired_contrast,
)
from fedact.domain.enums import MissingCutoffReason
from fedact.domain.records import SplitCutoffIdentity


def test_aggregate_cutoff_from_seeds_means_finite_seed_values() -> None:
    observations = (
        SeedLevelEndpointObservation(SplitCutoffIdentity("c1"), 1, 0.1, None),
        SeedLevelEndpointObservation(SplitCutoffIdentity("c1"), 2, 0.3, None),
    )
    aggregate = aggregate_cutoff_from_seeds(observations)
    assert aggregate.value == 0.2
    assert aggregate.missing_reason is None


def test_aggregate_cutoff_from_seeds_propagates_reason_when_all_missing() -> None:
    observations = (
        SeedLevelEndpointObservation(
            SplitCutoffIdentity("c1"), 1, None, MissingCutoffReason.NUMERICAL_FAILURE
        ),
        SeedLevelEndpointObservation(
            SplitCutoffIdentity("c1"), 2, None, MissingCutoffReason.NUMERICAL_FAILURE
        ),
    )
    aggregate = aggregate_cutoff_from_seeds(observations)
    assert aggregate.value is None
    assert aggregate.missing_reason is MissingCutoffReason.NUMERICAL_FAILURE


def test_aggregate_cutoff_from_seeds_ignores_missing_when_some_finite() -> None:
    observations = (
        SeedLevelEndpointObservation(SplitCutoffIdentity("c1"), 1, 0.5, None),
        SeedLevelEndpointObservation(
            SplitCutoffIdentity("c1"), 2, None, MissingCutoffReason.INFRASTRUCTURE_FAILURE
        ),
    )
    aggregate = aggregate_cutoff_from_seeds(observations)
    assert aggregate.value == 0.5


def test_build_paired_contrast_matches_only_shared_cutoffs() -> None:
    method_a = (
        CutoffAggregate(SplitCutoffIdentity("c1"), 0.5, None),
        CutoffAggregate(SplitCutoffIdentity("c2"), 0.4, None),
        CutoffAggregate(SplitCutoffIdentity("c3"), 0.6, None),
    )
    method_b = (
        CutoffAggregate(SplitCutoffIdentity("c1"), 0.3, None),
        CutoffAggregate(SplitCutoffIdentity("c2"), 0.2, None),
    )
    contrast = build_paired_contrast(
        method_a, method_b, minimum_paired_cutoffs=2, maximum_missing_cutoff_fraction=0.1
    )
    assert contrast.eligible_cutoff_count == 2
    assert contrast.paired_differences == (0.2, 0.2)
    assert contrast.sufficient


def test_build_paired_contrast_insufficient_below_minimum_cutoffs() -> None:
    method_a = (CutoffAggregate(SplitCutoffIdentity("c1"), 0.5, None),)
    method_b = (CutoffAggregate(SplitCutoffIdentity("c1"), 0.3, None),)
    contrast = build_paired_contrast(
        method_a, method_b, minimum_paired_cutoffs=6, maximum_missing_cutoff_fraction=0.1
    )
    assert not contrast.sufficient


def test_build_paired_contrast_insufficient_above_missing_fraction() -> None:
    method_a = (
        CutoffAggregate(SplitCutoffIdentity("c1"), 0.5, None),
        CutoffAggregate(SplitCutoffIdentity("c2"), None, MissingCutoffReason.NUMERICAL_FAILURE),
        CutoffAggregate(SplitCutoffIdentity("c3"), None, MissingCutoffReason.NUMERICAL_FAILURE),
    )
    method_b = (
        CutoffAggregate(SplitCutoffIdentity("c1"), 0.3, None),
        CutoffAggregate(SplitCutoffIdentity("c2"), 0.2, None),
        CutoffAggregate(SplitCutoffIdentity("c3"), 0.1, None),
    )
    contrast = build_paired_contrast(
        method_a, method_b, minimum_paired_cutoffs=1, maximum_missing_cutoff_fraction=0.1
    )
    assert contrast.missing_cutoff_count == 2
    assert not contrast.sufficient
