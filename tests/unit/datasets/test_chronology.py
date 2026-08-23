from __future__ import annotations

from pathlib import Path

import pytest

from fedact.config.loading import LoadedConfiguration, load_production_configuration
from fedact.config.models import FedActConfig
from fedact.datasets.chronology import (
    LAMDA_MISSING_2015_GAP,
    ChronologyError,
    HorizonAvailability,
    SourceChronology,
    SourceGap,
    calendar_month,
    classify_horizon_availability,
    confirmatory_outcome_for_cutoffs,
    endpoint_eligible_for_cutoff,
    enumerate_historical_endpoints,
    enumerate_rolling_cutoffs,
    interval_overlaps_gap,
    month_offset,
    reuse_source_checkpoint_month,
    transition_windows,
)
from fedact.domain.enums import ScientificOutcome

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PRODUCTION_CONFIGURATION = REPOSITORY_ROOT / "configs" / "fedact.yaml"


@pytest.fixture(scope="module")
def config() -> FedActConfig:
    loaded: LoadedConfiguration = load_production_configuration(PRODUCTION_CONFIGURATION)
    return loaded.values


def continuous_source() -> SourceChronology:
    return SourceChronology(
        first_observed_month=calendar_month(0), last_observed_month=calendar_month(60)
    )


def test_transition_windows_are_half_open_and_adjacent(config: FedActConfig) -> None:
    windows = transition_windows(calendar_month(9), config.temporal.transition_interval_months)
    assert windows.before_window_start_inclusive == 3
    assert windows.before_window_end_exclusive == 6
    assert windows.after_window_start_inclusive == 6
    assert windows.after_window_end_exclusive == 9
    assert windows.before_window_end_exclusive == windows.after_window_start_inclusive


def test_transition_endpoint_must_precede_two_full_windows() -> None:
    with pytest.raises(ChronologyError):
        transition_windows(calendar_month(5), 3)


def test_historical_interval_is_exactly_the_configured_window(config: FedActConfig) -> None:
    cutoff = 24
    window = config.temporal.historical_training_window_months
    historical_start = cutoff - window
    assert historical_start == 12
    assert endpoint_eligible_for_cutoff(calendar_month(11), calendar_month(cutoff), window) is False
    assert endpoint_eligible_for_cutoff(calendar_month(12), calendar_month(cutoff), window) is True
    assert endpoint_eligible_for_cutoff(calendar_month(23), calendar_month(cutoff), window) is True
    assert endpoint_eligible_for_cutoff(calendar_month(24), calendar_month(cutoff), window) is False


def test_lamda_2015_gap_is_a_hard_chronology_break() -> None:
    lamda = SourceChronology(
        first_observed_month=calendar_month(0),
        last_observed_month=calendar_month(143),
        prohibited_gaps=(LAMDA_MISSING_2015_GAP,),
    )
    assert lamda.interval_is_observable(calendar_month(20), calendar_month(24))
    assert not lamda.interval_is_observable(calendar_month(23), calendar_month(27))
    assert interval_overlaps_gap(calendar_month(22), calendar_month(30), LAMDA_MISSING_2015_GAP)


def test_intervals_may_not_bridge_documented_gaps() -> None:
    source = SourceChronology(
        first_observed_month=calendar_month(0),
        last_observed_month=calendar_month(60),
        prohibited_gaps=(
            SourceGap(
                gap_start_exclusive_month=calendar_month(29),
                gap_end_inclusive_month=calendar_month(31),
            ),
        ),
    )
    assert source.interval_is_observable(calendar_month(26), calendar_month(29))
    assert not source.interval_is_observable(calendar_month(26), calendar_month(32))


def test_rolling_cutoffs_are_derived_deterministically_from_the_release(
    config: FedActConfig,
) -> None:
    source = continuous_source()
    eligible = enumerate_rolling_cutoffs(source, config)
    assert len(eligible) >= 1
    months = [cutoff.cutoff_exclusive_month for cutoff in eligible]
    assert months == sorted(months)
    step = config.temporal.cutoff_step_months
    consecutive = list(zip(months, months[1:], strict=False))
    assert all(later - earlier == step for earlier, later in consecutive)
    expected_first = source.first_observed_month + config.temporal.historical_training_window_months
    assert months[0] == expected_first


def test_primary_confirmatory_requires_complete_later_real_interval(
    config: FedActConfig,
) -> None:
    source = SourceChronology(
        first_observed_month=calendar_month(0), last_observed_month=calendar_month(30)
    )
    eligible = enumerate_rolling_cutoffs(source, config)
    primary_horizon = config.temporal.primary_confirmatory_horizon_months
    for cutoff in eligible:
        complete = source.interval_is_observable(
            cutoff.cutoff_exclusive_month,
            month_offset(cutoff.cutoff_exclusive_month, primary_horizon),
        )
        assert cutoff.primary_confirmatory is complete


def test_unavailable_horizon_is_missing_source_data_and_never_shortened(
    config: FedActConfig,
) -> None:
    source = SourceChronology(
        first_observed_month=calendar_month(0), last_observed_month=calendar_month(30)
    )
    horizons = tuple(config.temporal.forecast_horizons_months)
    evaluations = classify_horizon_availability(source, calendar_month(24), horizons)
    by_horizon = {evaluation.horizon_months: evaluation.availability for evaluation in evaluations}
    for horizon in horizons:
        observable = source.interval_is_observable(
            calendar_month(24), month_offset(calendar_month(24), horizon)
        )
        expected = (
            HorizonAvailability.OBSERVABLE
            if observable
            else (HorizonAvailability.MISSING_SOURCE_DATA)
        )
        assert by_horizon[horizon] is expected
    long_missing = [
        evaluation
        for evaluation in evaluations
        if evaluation.availability is HorizonAvailability.MISSING_SOURCE_DATA
    ]
    assert long_missing, "the fixture must exercise a horizon beyond the acquired corpus"
    assert all(evaluation.horizon_months in horizons for evaluation in evaluations)


def test_duplicate_configured_horizons_are_rejected(config: FedActConfig) -> None:
    with pytest.raises(ChronologyError):
        classify_horizon_availability(
            continuous_source(),
            calendar_month(24),
            (config.temporal.early_horizon_months, config.temporal.early_horizon_months),
        )


def test_fewer_than_minimum_paired_cutoffs_is_insufficient_evidence(
    config: FedActConfig,
) -> None:
    minimum = config.statistics.minimum_paired_cutoffs
    assert confirmatory_outcome_for_cutoffs(minimum, minimum) is ScientificOutcome.PASS
    assert (
        confirmatory_outcome_for_cutoffs(minimum - 1, minimum)
        is ScientificOutcome.INSUFFICIENT_EVIDENCE
    )


def test_intermediate_cutoffs_reuse_most_recent_compatible_checkpoint(
    config: FedActConfig,
) -> None:
    interval = config.temporal.full_retraining_interval_months
    owner = 4 * interval
    intermediate = owner + 1
    assert reuse_source_checkpoint_month(calendar_month(intermediate), interval) == owner
    assert (
        reuse_source_checkpoint_month(calendar_month(owner + interval), interval)
        == owner + interval
    )
    with pytest.raises(ChronologyError):
        reuse_source_checkpoint_month(calendar_month(interval - 1), interval)


def test_enumerated_endpoints_respect_half_open_history_and_gaps(config: FedActConfig) -> None:
    source = SourceChronology(
        first_observed_month=calendar_month(0),
        last_observed_month=calendar_month(60),
        prohibited_gaps=(
            SourceGap(
                gap_start_exclusive_month=calendar_month(40),
                gap_end_inclusive_month=calendar_month(43),
            ),
        ),
    )
    endpoints = enumerate_historical_endpoints(source, calendar_month(48), config)
    assert endpoints == tuple(sorted(endpoints))
    delta = config.temporal.transition_interval_months
    history_start = 48 - config.temporal.historical_training_window_months
    for endpoint in endpoints:
        assert endpoint - 2 * delta >= history_start
        assert endpoint < 48
        windows = transition_windows(endpoint, delta)
        assert source.interval_is_observable(windows.before_window_start_inclusive, endpoint)


def test_empty_observability_interval_is_rejected() -> None:
    with pytest.raises(ChronologyError):
        continuous_source().interval_is_observable(calendar_month(10), calendar_month(10))
