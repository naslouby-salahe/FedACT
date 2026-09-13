from __future__ import annotations

from pathlib import Path

import pytest

from fedact.data.lamda_apk_features import (
    LamdaFeatureVocabularyError,
    load_lamda_feature_vocabulary,
)
from fedact.domain.types import LamdaFeatureCategory


def _write_mapping(tmp_path: Path, rows: list[tuple[int, str]]) -> Path:
    mapping_path = tmp_path / "feature_mapping.csv"
    lines = ["mapped_name,feature_name"]
    lines.extend(f"feat_{index},{feature_name}" for index, feature_name in rows)
    mapping_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return mapping_path


def test_vocabulary_orders_features_by_their_mapped_index(tmp_path: Path) -> None:
    mapping_path = _write_mapping(
        tmp_path,
        [
            (2, "ServiceList_com.example.SyncService"),
            (0, "ActivityList_com.example.MainActivity"),
            (1, "RequestedPermissionList_android.permission.CAMERA"),
        ],
    )
    vocabulary = load_lamda_feature_vocabulary(mapping_path)
    assert vocabulary.dimension == 3
    assert vocabulary.category_by_index == (
        LamdaFeatureCategory.ACTIVITY_LIST,
        LamdaFeatureCategory.REQUESTED_PERMISSION_LIST,
        LamdaFeatureCategory.SERVICE_LIST,
    )
    assert vocabulary.name_by_index == (
        "com.example.MainActivity",
        "android.permission.CAMERA",
        "com.example.SyncService",
    )


def test_vocabulary_marks_unverifiable_feature_indices(tmp_path: Path) -> None:
    mapping_path = _write_mapping(
        tmp_path,
        [
            (0, "ActivityList_com.example.MainActivity"),
            (1, "UsedPermissionsList_android.permission.CAMERA"),
            (2, "BroadcastReceiverList_com.example.BootReceiver"),
        ],
    )
    vocabulary = load_lamda_feature_vocabulary(mapping_path)
    assert vocabulary.unverifiable_indices == frozenset({1})


def test_vocabulary_rejects_a_feature_outside_every_known_category(tmp_path: Path) -> None:
    mapping_path = _write_mapping(tmp_path, [(0, "UnknownCategory_something")])
    with pytest.raises(LamdaFeatureVocabularyError, match="does not match any known"):
        load_lamda_feature_vocabulary(mapping_path)
