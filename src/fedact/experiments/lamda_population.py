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
    raw_root = (
        application.repository_root
        / application.configuration.values.workspace.lamda_release_directory
    )
    if not raw_root.is_dir():
        LOGGER.warning("LAMDA population load has no release at %s", raw_root)
        return None
    loaded = load_lamda_records(
        raw_root,
        application.configuration.values.datasets.lamda.preprocessing.feature_column_prefix,
    )
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


def eligible_cutoffs(
    application: ExperimentRuntime, population: LamdaPopulation
) -> tuple[int, ...]:
    config = application.configuration.values
    horizon = config.temporal.primary_confirmatory_horizon_months
    history = config.temporal.historical_training_window_months
    minimum = config.identification.minimum_support_per_class
    eligible: list[int] = []
    for cutoff in range(int(population.months.min()), int(population.months.max()) - horizon + 1):
        historical = (population.months >= cutoff - history) & (population.months < cutoff)
        later = (population.months >= cutoff) & (population.months < cutoff + horizon)
        if not historical.any() or not later.any():
            continue
        historical_labels = population.labels[historical]
        later_labels = population.labels[later]
        if (
            np.count_nonzero(historical_labels) >= minimum
            and np.count_nonzero(~historical_labels) >= minimum
            and np.count_nonzero(later_labels) > 0
            and np.count_nonzero(~later_labels) > 0
        ):
            eligible.append(cutoff)
    return tuple(eligible)
