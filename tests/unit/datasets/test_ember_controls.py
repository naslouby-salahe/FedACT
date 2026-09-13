from __future__ import annotations

import pytest

from fedact.data.ember2024 import (
    ControlMatchingLevel,
    DisplacementVector,
    EmberControlRecord,
    choose_control_matching_level,
    conservative_timestamp_month,
    is_degenerate_displacement,
    match_ember_controls,
    monthly_matching_cell,
)
from fedact.domain.types import SampleIdentifier, WeekIdentifier

JANUARY_WEEK = WeekIdentifier("2023-01-1")
JANUARY_LATER_WEEK = WeekIdentifier("2023-01-3")
FEBRUARY_WEEK = WeekIdentifier("2023-02-1")
WEEKLY = ControlMatchingLevel(weekly=True)
MONTHLY = ControlMatchingLevel(weekly=False)
MINIMUM_SUPPORT = 200


def _record(sample_id: str, week: WeekIdentifier) -> EmberControlRecord:
    return EmberControlRecord(
        sample_hash=SampleIdentifier(sample_id),
        format_client="pe",
        collection_week=week,
        family="berbew",
    )


def test_monthly_matching_cell_truncates_a_week_to_its_month() -> None:
    assert monthly_matching_cell(JANUARY_WEEK) == "2023-01"


def test_conservative_timestamp_month_preserves_the_week() -> None:
    assert conservative_timestamp_month(JANUARY_WEEK) == JANUARY_WEEK


def test_control_matching_prefers_weekly_then_monthly_then_abstains() -> None:
    assert choose_control_matching_level(MINIMUM_SUPPORT, MINIMUM_SUPPORT, 0) == WEEKLY
    assert choose_control_matching_level(0, MINIMUM_SUPPORT, MINIMUM_SUPPORT) == MONTHLY
    assert choose_control_matching_level(0, MINIMUM_SUPPORT, 0) is None


def test_weekly_matching_pairs_records_from_the_same_week() -> None:
    matches = match_ember_controls(
        (_record("malicious-1", JANUARY_WEEK),),
        (_record("control-1", JANUARY_WEEK), _record("control-2", FEBRUARY_WEEK)),
        WEEKLY,
    )
    assert len(matches) == 1
    assert matches[0].malicious_sample_id == "malicious-1"
    assert matches[0].control_sample_id == "control-1"
    assert matches[0].matched_week == JANUARY_WEEK
    assert matches[0].matched_month is None
    assert matches[0].weekly_level is True


def test_monthly_matching_pairs_records_within_the_same_month() -> None:
    matches = match_ember_controls(
        (_record("malicious-1", JANUARY_WEEK),),
        (_record("control-1", JANUARY_LATER_WEEK),),
        MONTHLY,
    )
    assert len(matches) == 1
    assert matches[0].control_sample_id == "control-1"
    assert matches[0].matched_week is None
    assert matches[0].matched_month == "2023-01"
    assert matches[0].weekly_level is False


def test_a_control_record_is_consumed_at_most_once() -> None:
    matches = match_ember_controls(
        (_record("malicious-1", JANUARY_WEEK), _record("malicious-2", JANUARY_WEEK)),
        (_record("control-1", JANUARY_WEEK),),
        WEEKLY,
    )
    assert [match.control_sample_id for match in matches] == ["control-1"]


def test_records_without_a_control_in_their_cell_are_omitted() -> None:
    matches = match_ember_controls(
        (_record("malicious-1", JANUARY_WEEK),),
        (_record("control-1", FEBRUARY_WEEK),),
        WEEKLY,
    )
    assert matches == ()


def test_monthly_matching_never_crosses_a_month_boundary() -> None:
    matches = match_ember_controls(
        (_record("malicious-1", JANUARY_WEEK),),
        (_record("control-1", FEBRUARY_WEEK),),
        MONTHLY,
    )
    assert matches == ()


def test_displacement_norm_is_the_euclidean_length() -> None:
    assert DisplacementVector(components=(3.0, 4.0)).displacement_norm() == pytest.approx(5.0)


def test_normalized_displacement_has_unit_norm() -> None:
    normalized = DisplacementVector(components=(3.0, 4.0)).normalized()
    assert normalized.displacement_norm() == pytest.approx(1.0)
    assert normalized.components[0] == pytest.approx(0.6)


def test_normalizing_a_zero_displacement_is_rejected() -> None:
    with pytest.raises(ValueError, match="cannot normalize a zero displacement vector"):
        DisplacementVector(components=(0.0, 0.0)).normalized()


def test_degenerate_displacement_is_measured_against_the_floor() -> None:
    assert is_degenerate_displacement(DisplacementVector(components=(0.0, 0.0)), 1.0e-9) is True
    assert is_degenerate_displacement(DisplacementVector(components=(1.0, 0.0)), 1.0e-9) is False
