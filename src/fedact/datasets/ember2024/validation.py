from __future__ import annotations

import numpy as np

from fedact.datasets.ember2024.loader import LoadedEmberDataset
from fedact.datasets.ember2024.preprocessing import (
    apply_log1p_transforms,
    standardize_ember_features,
)


class EmberValidationError(ValueError):
    pass


def validate_ember_dataset(dataset: LoadedEmberDataset) -> None:
    if len(dataset.records) != dataset.features.shape[0]:
        raise EmberValidationError("record count and feature rows must match")


def run_empty_ember_transform_audit() -> None:
    empty = LoadedEmberDataset(records=(), features=np.zeros((0, 0), dtype=np.float32))
    validate_ember_dataset(empty)
    transformed = apply_log1p_transforms(empty.features, np.zeros(0, dtype=bool))
    standardized = standardize_ember_features(transformed)
    if standardized.shape[0] < 0:
        raise EmberValidationError("EMBER standardization produced an impossible shape")
