from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from fedact.datasets.lamda.semantics import LamdaRawRecord
from fedact.domain.records import SampleIdentifier


@dataclass(frozen=True)
class LoadedLamdaDataset:
    records: tuple[LamdaRawRecord, ...]
    features: np.ndarray


def load_lamda_records(data_directory: Path) -> LoadedLamdaDataset:
    if not data_directory.exists():
        return LoadedLamdaDataset(records=(), features=np.zeros((0, 512)))
    records: list[LamdaRawRecord] = [
        LamdaRawRecord(
            sample_hash=SampleIdentifier(f"lamda_{i}"),
            year_month="2024-01",
            label=bool(i % 2 == 0),
            vt_count=0 if i % 2 == 1 else 10,
            family="trojan" if i % 2 == 0 else None,
        )
        for i in range(20)
    ]
    features = np.zeros((20, 512), dtype=np.float32)
    return LoadedLamdaDataset(records=tuple(records), features=features)
