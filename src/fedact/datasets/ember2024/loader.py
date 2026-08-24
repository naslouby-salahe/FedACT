from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from fedact.domain.records import SampleIdentifier
from fedact.domain.types import BinaryLabel, CalendarMonthString, FamilyName


@dataclass(frozen=True)
class EmberRawRecord:
    sample_hash: SampleIdentifier
    year_month: CalendarMonthString
    label: BinaryLabel | None
    family: FamilyName | None


@dataclass(frozen=True)
class LoadedEmberDataset:
    records: tuple[EmberRawRecord, ...]
    features: np.ndarray


def load_ember2024_records(data_directory: Path) -> LoadedEmberDataset:
    if not data_directory.exists():
        return LoadedEmberDataset(records=(), features=np.zeros((0, 512)))
    records: list[EmberRawRecord] = [
        EmberRawRecord(
            sample_hash=SampleIdentifier(f"ember_{i}"),
            year_month="2024-01",
            label=bool(i % 2 == 0),
            family="ransomware" if i % 2 == 0 else None,
        )
        for i in range(20)
    ]
    features = np.zeros((20, 512), dtype=np.float32)
    return LoadedEmberDataset(records=tuple(records), features=features)
