from __future__ import annotations

from pathlib import Path

import numpy as np

from fedact.data.ember2024 import (
    EmberRawRecord,
    apply_log1p_transforms,
    control_transition_replicates,
    ember2024_count_feature_mask,
    load_ember2024_records,
    malicious_transition_displacement,
    standardize_ember_features,
    validate_ember_dataset,
    year_month_to_calendar_month,
)
from fedact.data.splits import calendar_month
from fedact.domain.types import SampleIdentifier, WindowSpanMonths


def test_ember2024_dataset_pipeline_on_empty_directory(tmp_path: Path) -> None:
    ds = load_ember2024_records(tmp_path)
    validate_ember_dataset(ds)
    assert ds.records == ()
    assert ds.features.shape == (0, ember2024_count_feature_mask().size)


def test_count_feature_mask_matches_feature_vector_dimension() -> None:
    mask = ember2024_count_feature_mask()
    assert mask.dtype == np.bool_
    assert 0 < mask.sum() < mask.size


def test_apply_log1p_transforms_only_touches_count_columns() -> None:
    mask = np.array([True, False, True])
    features = np.array([[3.0, -1.0, 8.0], [15.0, 2.0, 0.0]], dtype=np.float32)
    transformed = apply_log1p_transforms(features, mask)
    assert np.allclose(transformed[:, 0], np.log1p(features[:, 0]))
    assert np.allclose(transformed[:, 1], features[:, 1])
    assert np.allclose(transformed[:, 2], np.log1p(features[:, 2]))


def test_apply_log1p_transforms_clips_negative_counts_to_zero() -> None:
    mask = np.array([True])
    features = np.array([[-5.0]], dtype=np.float32)
    transformed = apply_log1p_transforms(features, mask)
    assert transformed[0, 0] == 0.0


def test_standardize_ember_features_produces_zero_mean_unit_variance() -> None:
    feats = np.abs(np.random.default_rng(0).standard_normal((10, 20))).astype(np.float32)
    standardized = standardize_ember_features(feats)
    assert standardized.shape == feats.shape
    assert np.allclose(np.mean(standardized, axis=0), 0.0, atol=1e-5)


def test_year_month_to_calendar_month_uses_the_real_acquired_epoch() -> None:
    assert year_month_to_calendar_month("2023-09") == 0
    assert year_month_to_calendar_month("2023-12") == 3
    assert year_month_to_calendar_month("2024-01") == 4
    assert year_month_to_calendar_month("2024-12") == 15


def _labeled_records_and_features() -> tuple[tuple[EmberRawRecord, ...], np.ndarray]:
    records: list[EmberRawRecord] = []
    features: list[list[float]] = []
    for year_month, label in (("2023-09", True), ("2023-10", True)):
        for sample_index in range(20):
            records.append(
                EmberRawRecord(
                    sample_hash=SampleIdentifier(f"{year_month}-{sample_index}"),
                    year_month=year_month,
                    label=label,
                    family=None,
                )
            )
            features.append([float(sample_index), 0.0])
    for year_month, label in (("2023-09", False), ("2023-10", False)):
        for sample_index in range(20):
            records.append(
                EmberRawRecord(
                    sample_hash=SampleIdentifier(f"{year_month}-control-{sample_index}"),
                    year_month=year_month,
                    label=label,
                    family=None,
                )
            )
            features.append([float(sample_index), 1.0])
    return tuple(records), np.array(features, dtype=np.float64)


def test_malicious_transition_displacement_uses_direct_binary_label() -> None:
    records, features = _labeled_records_and_features()
    endpoint = calendar_month(2)
    interval: WindowSpanMonths = 1
    result = malicious_transition_displacement(records, features, endpoint, interval)
    assert result is not None
    assert result.support_before == 20
    assert result.support_after == 20
    assert np.allclose(result.displacement, np.array([0.0, 0.0]))


def test_control_transition_replicates_excludes_malicious_records() -> None:
    records, features = _labeled_records_and_features()
    endpoint = calendar_month(2)
    interval: WindowSpanMonths = 1
    replicates = control_transition_replicates(records, features, (endpoint,), interval)
    assert len(replicates) == 1
    assert replicates[0].support_before == 20
    assert replicates[0].support_after == 20
