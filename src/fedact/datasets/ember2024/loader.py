from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import numpy as np

from fedact.domain.records import SampleIdentifier
from fedact.domain.types import BinaryLabel, CalendarMonthString, FamilyName

_HISTOGRAM_BIN_COUNT = 256
_BYTEENTROPY_BIN_COUNT = 256


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


def _year_month_from_epoch_seconds(epoch_seconds: float) -> CalendarMonthString:
    moment = datetime.fromtimestamp(epoch_seconds, tz=UTC)
    return f"{moment.year:04d}-{moment.month:02d}"


def _parse_record(payload: dict[str, object]) -> tuple[EmberRawRecord, list[float]]:
    sha256 = cast(str, payload["sha256"])
    raw_label = cast(int, payload["label"])
    submission_epoch = cast(float, payload["first_submission_date"])
    family = cast(str | None, payload.get("family"))
    histogram = cast(list[int], payload["histogram"])
    byteentropy = cast(list[int], payload["byteentropy"])
    record = EmberRawRecord(
        sample_hash=SampleIdentifier(sha256),
        year_month=_year_month_from_epoch_seconds(submission_epoch),
        label=None if raw_label < 0 else bool(raw_label),
        family=family,
    )
    feature_row = [float(value) for value in histogram] + [float(value) for value in byteentropy]
    return record, feature_row


def load_ember2024_records(data_directory: Path) -> LoadedEmberDataset:
    feature_dimension = _HISTOGRAM_BIN_COUNT + _BYTEENTROPY_BIN_COUNT
    jsonl_files = sorted(data_directory.glob("*.jsonl"))
    if not jsonl_files:
        return LoadedEmberDataset(records=(), features=np.zeros((0, feature_dimension)))
    records: list[EmberRawRecord] = []
    feature_rows: list[list[float]] = []
    for jsonl_file in jsonl_files:
        with jsonl_file.open(encoding="utf-8") as jsonl_stream:
            for line in jsonl_stream:
                stripped = line.strip()
                if not stripped:
                    continue
                payload = cast(dict[str, object], json.loads(stripped))
                record, feature_row = _parse_record(payload)
                records.append(record)
                feature_rows.append(feature_row)
    features = np.array(feature_rows, dtype=np.float32).reshape((len(records), feature_dimension))
    return LoadedEmberDataset(records=tuple(records), features=features)
