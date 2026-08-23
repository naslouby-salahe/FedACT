from __future__ import annotations

from fedact.datasets.lamda.loader import LoadedLamdaDataset


class LamdaValidationError(ValueError):
    pass


def validate_lamda_dataset(dataset: LoadedLamdaDataset) -> None:
    if len(dataset.records) != dataset.features.shape[0]:
        raise LamdaValidationError("record count and feature rows must match")
