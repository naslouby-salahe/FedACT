from __future__ import annotations

from fedact.datasets.ember2024.loader import LoadedEmberDataset


class EmberValidationError(ValueError):
    pass


def validate_ember_dataset(dataset: LoadedEmberDataset) -> None:
    if len(dataset.records) != dataset.features.shape[0]:
        raise EmberValidationError("record count and feature rows must match")
