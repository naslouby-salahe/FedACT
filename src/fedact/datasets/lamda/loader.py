from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd

from fedact.datasets.lamda.semantics import LamdaRawRecord
from fedact.domain.records import SampleIdentifier

_FEATURE_COLUMN_PREFIX = "feat_"


@dataclass(frozen=True)
class LoadedLamdaDataset:
    records: tuple[LamdaRawRecord, ...]
    features: np.ndarray


def _feature_columns(columns: list[str]) -> list[str]:
    return sorted(
        (column for column in columns if column.startswith(_FEATURE_COLUMN_PREFIX)),
        key=lambda column: int(column.removeprefix(_FEATURE_COLUMN_PREFIX)),
    )


def load_lamda_records(data_directory: Path) -> LoadedLamdaDataset:
    parquet_files = sorted(data_directory.glob("*.parquet"))
    if not parquet_files:
        return LoadedLamdaDataset(records=(), features=np.zeros((0, 0), dtype=np.float32))
    combined = pd.concat((pd.read_parquet(path) for path in parquet_files), ignore_index=True)
    columns = cast(list[str], combined.columns.tolist())
    feature_columns = _feature_columns(columns)
    features = cast(np.ndarray, combined[feature_columns].to_numpy(dtype=np.float32))
    hashes = cast(list[str], combined["hash"].tolist())
    year_months = cast(list[str], combined["year_month"].tolist())
    labels = cast(list[float], combined["label"].tolist())
    vt_counts = cast(list[float], combined["vt_count"].tolist())
    families = cast(list[str], combined["family"].tolist())
    records = tuple(
        LamdaRawRecord(
            sample_hash=SampleIdentifier(sample_hash),
            year_month=year_month,
            label=None if pd.isna(label) else bool(label),
            vt_count=None if pd.isna(vt_count) else round(vt_count),
            family=None if pd.isna(family) else family,
        )
        for sample_hash, year_month, label, vt_count, family in zip(
            hashes, year_months, labels, vt_counts, families, strict=True
        )
    )
    return LoadedLamdaDataset(records=records, features=features)
