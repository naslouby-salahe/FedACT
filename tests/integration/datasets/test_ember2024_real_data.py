from __future__ import annotations

import shutil
from pathlib import Path

import numpy as np
import pytest

from fedact.datasets.ember2024.loader import (
    LoadedEmberDataset,
    ember2024_count_feature_mask,
    load_ember2024_records,
)
from fedact.datasets.ember2024.preprocessing import (
    apply_log1p_transforms,
    standardize_ember_features,
)

EMBER2024_DIRECTORY = Path(__file__).resolve().parents[3] / "data" / "raw" / "EMBER2024"

pytestmark = pytest.mark.skipif(
    not EMBER2024_DIRECTORY.is_dir(), reason="data/raw/EMBER2024 is not available"
)


def _load_single_real_shard(tmp_path: Path) -> LoadedEmberDataset:
    jsonl_files = sorted(EMBER2024_DIRECTORY.glob("*.jsonl"))
    assert jsonl_files, "expected at least one real EMBER2024 jsonl file"
    shutil.copy(jsonl_files[0], tmp_path / jsonl_files[0].name)
    return load_ember2024_records(tmp_path)


def test_load_ember2024_records_produces_real_finite_feature_vectors(tmp_path: Path) -> None:
    loaded = _load_single_real_shard(tmp_path)
    assert len(loaded.records) > 0
    assert loaded.features.shape[1] == ember2024_count_feature_mask().size
    assert np.isfinite(loaded.features).all()
    labels = {record.label for record in loaded.records}
    assert labels <= {True, False, None}


def test_ember2024_preprocessing_pipeline_on_real_features(tmp_path: Path) -> None:
    loaded = _load_single_real_shard(tmp_path)
    mask = ember2024_count_feature_mask()
    log_transformed = apply_log1p_transforms(loaded.features, mask)
    assert np.isfinite(log_transformed).all()
    standardized = standardize_ember_features(log_transformed)
    assert standardized.shape == loaded.features.shape
    assert np.isfinite(standardized).all()
