from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np

from fedact.data.lamda import (
    audited_label,
    label_derivation_rule,
    load_lamda_records,
    validate_lamda_dataset,
    year_month_to_calendar_month,
)
from fedact.domain.types import FamilyName, SampleIdentifier
from fedact.experiments.registry import ExperimentRuntime

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class LamdaPopulation:
    features: np.ndarray
    labels: np.ndarray
    months: np.ndarray
    sample_ids: tuple[SampleIdentifier, ...]
    family: tuple[FamilyName | None, ...]


def load_lamda_population(application: ExperimentRuntime) -> LamdaPopulation | None:
    raw_root = application.repository_root / "data" / "raw" / "LAMDA" / "Baseline" / "2023"
    if not raw_root.is_dir():
        LOGGER.warning("LAMDA population load has no release at %s", raw_root)
        return None
    loaded = load_lamda_records(raw_root)
    validate_lamda_dataset(loaded)
    rule = label_derivation_rule(application.configuration.values.datasets.lamda)
    keep = np.fromiter(
        (audited_label(rule, record).binary_label is not None for record in loaded.records),
        dtype=bool,
        count=len(loaded.records),
    )
    if not np.any(keep):
        LOGGER.warning("LAMDA contains no rows with an auditable binary label")
        return None
    records = tuple(
        record for record, retained in zip(loaded.records, keep, strict=True) if retained
    )
    labels = np.fromiter(
        (bool(audited_label(rule, record).binary_label) for record in records),
        dtype=bool,
        count=len(records),
    )
    months = np.fromiter(
        (int(year_month_to_calendar_month(record.year_month)) for record in records),
        dtype=np.int64,
        count=len(records),
    )
    return LamdaPopulation(
        features=np.ascontiguousarray(loaded.features[keep], dtype=np.float64),
        labels=labels,
        months=months,
        sample_ids=tuple(record.sample_hash for record in records),
        family=tuple(record.family for record in records),
    )
