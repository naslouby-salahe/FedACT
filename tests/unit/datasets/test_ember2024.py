from __future__ import annotations

from pathlib import Path

import numpy as np

from fedact.datasets.ember2024.loader import load_ember2024_records
from fedact.datasets.ember2024.preprocessing import (
    apply_log1p_transforms,
    standardize_ember_features,
)
from fedact.datasets.ember2024.validation import validate_ember_dataset


def test_ember2024_dataset_pipeline(tmp_path: Path) -> None:
    ds = load_ember2024_records(tmp_path)
    validate_ember_dataset(ds)
    feats = np.abs(np.random.randn(10, 20)).astype(np.float32)
    transformed = apply_log1p_transforms(feats)
    assert np.all(transformed >= 0.0)
    standardized = standardize_ember_features(transformed)
    assert standardized.shape == feats.shape
