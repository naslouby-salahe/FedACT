from __future__ import annotations

from pathlib import Path

import numpy as np

from fedact.datasets.ember2024.loader import ember2024_count_feature_mask, load_ember2024_records
from fedact.datasets.ember2024.preprocessing import (
    apply_log1p_transforms,
    standardize_ember_features,
)
from fedact.datasets.ember2024.validation import validate_ember_dataset


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
