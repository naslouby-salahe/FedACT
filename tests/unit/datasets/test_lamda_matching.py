from __future__ import annotations

import numpy as np
import pytest

from fedact.data.lamda import (
    LamdaRawRecord,
    LoadedLamdaDataset,
    MatchBudget,
    filter_low_variance_features,
    lamda_schema_manifest,
    match_controls_by_calendar_month,
    standardize_features,
    validate_lamda_dataset,
)
from fedact.domain.types import MaximumMatchesPerSample, SampleIdentifier

JANUARY = "2023-01"
FEBRUARY = "2023-02"
VARIANCE_THRESHOLD = 1.0e-6


def _record(sample_id: str, year_month: str) -> LamdaRawRecord:
    return LamdaRawRecord(
        sample_hash=SampleIdentifier(sample_id),
        year_month=year_month,
        label=True,
        vt_count=9,
        family="berbew",
    )


def _budget(maximum: int) -> MatchBudget:
    return MatchBudget(maximum_per_malicious=MaximumMatchesPerSample(maximum))


def test_controls_are_matched_within_the_same_calendar_month() -> None:
    matches = match_controls_by_calendar_month(
        (_record("malicious-1", JANUARY),),
        (_record("control-1", JANUARY), _record("control-2", FEBRUARY)),
        _budget(1),
    )
    assert len(matches) == 1
    assert matches[0].malicious_sample_id == "malicious-1"
    assert matches[0].control_sample_id == "control-1"
    assert matches[0].calendar_month == JANUARY


def test_each_malicious_record_may_consume_several_controls_within_budget() -> None:
    controls = tuple(_record(f"control-{index}", JANUARY) for index in range(3))
    matches = match_controls_by_calendar_month(
        (_record("malicious-1", JANUARY),), controls, _budget(2)
    )
    assert [match.control_sample_id for match in matches] == ["control-0", "control-1"]


def test_a_control_record_is_consumed_at_most_once() -> None:
    matches = match_controls_by_calendar_month(
        (_record("malicious-1", JANUARY), _record("malicious-2", JANUARY)),
        (_record("control-1", JANUARY),),
        _budget(3),
    )
    assert [match.control_sample_id for match in matches] == ["control-1"]


def test_malicious_records_without_a_same_month_control_are_omitted() -> None:
    matches = match_controls_by_calendar_month(
        (_record("malicious-1", JANUARY),),
        (_record("control-1", FEBRUARY),),
        _budget(1),
    )
    assert matches == ()


def test_low_variance_filtering_of_an_empty_matrix_is_a_no_op() -> None:
    empty = np.zeros((0, 3), dtype=np.float32)
    assert filter_low_variance_features(empty, VARIANCE_THRESHOLD) is empty


def test_low_variance_filtering_keeps_the_matrix_when_all_columns_are_flat() -> None:
    flat = np.ones((4, 2), dtype=np.float32)
    kept = filter_low_variance_features(flat, VARIANCE_THRESHOLD)
    assert kept.shape == flat.shape


def test_low_variance_filtering_drops_only_flat_columns() -> None:
    matrix = np.array([[0.0, 5.0], [1.0, 5.0], [0.0, 5.0], [1.0, 5.0]], dtype=np.float32)
    kept = filter_low_variance_features(matrix, VARIANCE_THRESHOLD)
    assert kept.shape == (4, 1)
    assert np.allclose(kept[:, 0], matrix[:, 0])


def test_standardizing_an_empty_matrix_is_a_no_op() -> None:
    empty = np.zeros((0, 3), dtype=np.float32)
    assert standardize_features(empty) is empty


def test_standardization_centres_and_scales_columns() -> None:
    matrix = np.array([[0.0, 10.0], [2.0, 10.0], [4.0, 10.0]], dtype=np.float64)
    standardized = standardize_features(matrix)
    assert np.allclose(standardized.mean(axis=0)[0], 0.0)
    assert standardized.std(axis=0)[0] == pytest.approx(1.0)
    assert np.allclose(standardized[:, 1], 0.0)


def test_validate_lamda_dataset_rejects_a_row_count_mismatch() -> None:
    mismatched = LoadedLamdaDataset(
        records=(_record("sample-1", JANUARY),),
        features=np.zeros((2, 3), dtype=np.float32),
    )
    with pytest.raises(ValueError, match="record count and feature rows must match"):
        validate_lamda_dataset(mismatched)


def test_validate_lamda_dataset_accepts_aligned_rows() -> None:
    aligned = LoadedLamdaDataset(
        records=(_record("sample-1", JANUARY),),
        features=np.zeros((1, 3), dtype=np.float32),
    )
    validate_lamda_dataset(aligned)


def test_schema_manifest_of_an_empty_population_starts_at_the_epoch() -> None:
    manifest = lamda_schema_manifest((), np.zeros((0, 3), dtype=np.float32))
    assert manifest.first_observed_month == 0
    assert manifest.last_observed_month == 0
    assert manifest.observed_row_count == 0


def test_schema_manifest_records_the_observed_month_span() -> None:
    records = (_record("sample-1", JANUARY), _record("sample-2", FEBRUARY))
    manifest = lamda_schema_manifest(records, np.zeros((2, 3), dtype=np.float32))
    assert manifest.first_observed_month <= manifest.last_observed_month
    assert manifest.observed_row_count == 2
