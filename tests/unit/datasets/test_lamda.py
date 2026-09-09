from __future__ import annotations

from pathlib import Path

import numpy as np

from fedact.data.lamda import load_lamda_records
from fedact.data.lamda import filter_low_variance_features, standardize_features
from fedact.data.lamda import validate_lamda_dataset


def test_lamda_dataset_pipeline(tmp_path: Path) -> None:
    ds = load_lamda_records(tmp_path)
    validate_lamda_dataset(ds)
    feats = np.random.randn(10, 20).astype(np.float32)
    filtered = filter_low_variance_features(feats, variance_threshold=1e-4)
    assert filtered.shape[1] <= 20
    standardized = standardize_features(filtered)
    assert standardized.shape == filtered.shape
