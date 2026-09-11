from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import NewType, cast

import numpy as np
import pandas as pd

from fedact.config.models import LamdaDatasetConfig
from fedact.data.records import (
    ClientSemanticsAudit,
    LabelDerivationRule,
    SchemaChronologyManifest,
    SchemaManifestField,
    corpus_level_client_audit,
)
from fedact.data.splits import (
    CalendarMonth,
    ControlTransitionReplicate,
    TransitionDisplacement,
    calendar_month,
    transition_windows,
    windowed_mean,
    year_month_ordinal,
)
from fedact.domain.types import (
    BinaryLabel,
    CalendarMonthString,
    DataAvailabilityFlag,
    DatasetIdentity,
    DatasetSelector,
    EligibilityFlag,
    FamilyName,
    Fraction,
    Probability,
    SampleCount,
    SampleIdentifier,
    ThresholdValue,
    VarianceThreshold,
    WindowSpanMonths,
)

_FEATURE_COLUMN_PREFIX = "feat_" #TODO: should be retrieved from yml and accessed through config. Identify any similar issues and fix it


@dataclass(frozen=True)
class LoadedLamdaDataset:
    records: tuple[LamdaRawRecord, ...]
    features: np.ndarray


def _feature_columns(columns: list[str]) -> list[str]: #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    return sorted(
        (column for column in columns if column.startswith(_FEATURE_COLUMN_PREFIX)),
        key=lambda column: int(column.removeprefix(_FEATURE_COLUMN_PREFIX)),
    )


def load_lamda_records(data_directory: Path) -> LoadedLamdaDataset:
    parquet_files = sorted(data_directory.rglob("*.parquet"))
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


def filter_low_variance_features(
    features: np.ndarray, variance_threshold: VarianceThreshold
) -> np.ndarray:
    if features.shape[0] == 0:
        return features
    variances = np.var(features, axis=0)
    keep = variances >= variance_threshold
    if not np.any(keep):
        return features
    return features[:, keep]


def standardize_features(features: np.ndarray) -> np.ndarray:
    if features.shape[0] == 0:
        return features
    mean = np.mean(features, axis=0)
    std = np.std(features, axis=0)
    std[std < 1e-12] = 1.0
    return (features - mean) / std


_LAMDA_EPOCH_YEAR_MONTH: CalendarMonthString = "2013-01"


@dataclass(frozen=True)
class LamdaRawRecord:
    sample_hash: SampleIdentifier
    year_month: CalendarMonthString
    label: BinaryLabel | None
    vt_count: SampleCount | None
    family: FamilyName | None


def label_derivation_rule(config: LamdaDatasetConfig) -> LabelDerivationRule:
    return LabelDerivationRule(
        benign_detection_count=config.labels.benign_detection_count,
        malware_minimum_detection_count=config.labels.malware_minimum_detection_count,
        discard_detection_counts=tuple(config.labels.discard_detection_counts),
    )


@dataclass(frozen=True)
class LabelAuditOutcome:
    binary_label: BinaryLabel | None


def audited_label(rule: LabelDerivationRule, record: LamdaRawRecord) -> LabelAuditOutcome:
    if record.label is not None and record.vt_count is not None:
        expected = _expected_label(rule, record.vt_count)
        if expected is None or expected != record.label:
            return LabelAuditOutcome(binary_label=None)
        return LabelAuditOutcome(binary_label=record.label)
    if record.label is not None:
        return LabelAuditOutcome(binary_label=record.label)
    if record.vt_count is not None:
        return LabelAuditOutcome(binary_label=_expected_label(rule, record.vt_count))
    return LabelAuditOutcome(binary_label=None)


def _expected_label(rule: LabelDerivationRule, vt_count: SampleCount) -> BinaryLabel | None:
    if vt_count == rule.benign_detection_count:
        return False
    if vt_count >= rule.malware_minimum_detection_count:
        return True
    if vt_count in rule.discard_detection_counts:
        return None
    return None


@dataclass(frozen=True)
class LamdaControlMatch:
    malicious_sample_id: SampleIdentifier
    control_sample_id: SampleIdentifier
    calendar_month: CalendarMonthString


MaximumMatchesPerSample = NewType("MaximumMatchesPerSample", int)


@dataclass(frozen=True)
class MatchBudget:
    maximum_per_malicious: MaximumMatchesPerSample


def match_controls_by_calendar_month(
    malicious: tuple[LamdaRawRecord, ...],
    controls: tuple[LamdaRawRecord, ...],
    budget: MatchBudget,
) -> tuple[LamdaControlMatch, ...]:
    controls_by_month: dict[str, list[LamdaRawRecord]] = {} #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    for control in controls:
        controls_by_month.setdefault(control.year_month, []).append(control)
    matches: list[LamdaControlMatch] = []
    used: set[SampleIdentifier] = set()
    for record in malicious:
        candidates = [
            control
            for control in controls_by_month.get(record.year_month, [])
            if control.sample_hash not in used
        ][: budget.maximum_per_malicious]
        for control in candidates:
            used.add(control.sample_hash)
            matches.append(
                LamdaControlMatch(
                    malicious_sample_id=record.sample_hash,
                    control_sample_id=control.sample_hash,
                    calendar_month=record.year_month,
                )
            )
    return tuple(matches)


def lamda_client_semantics() -> ClientSemanticsAudit:
    return corpus_level_client_audit(DatasetSelector.LAMDA)


@dataclass(frozen=True)
class OperatorEligibility:
    has_matching_raw_artifact: DataAvailabilityFlag

    def is_eligible(self) -> EligibilityFlag:
        return self.has_matching_raw_artifact


def year_month_to_calendar_month(year_month: CalendarMonthString) -> CalendarMonth:
    return year_month_ordinal(year_month, _LAMDA_EPOCH_YEAR_MONTH)


def _labeled_months(
    records: Sequence[LamdaRawRecord],
    rule: LabelDerivationRule,
    want_malicious: bool,
) -> tuple[np.ndarray, np.ndarray]:
    months = np.fromiter(
        (int(year_month_to_calendar_month(record.year_month)) for record in records),
        dtype=np.int64,
        count=len(records),
    )
    keep = np.fromiter(
        (audited_label(rule, record).binary_label is want_malicious for record in records),
        dtype=bool,
        count=len(records),
    )
    return months, keep


def malicious_transition_displacement(
    records: Sequence[LamdaRawRecord],
    features: np.ndarray,
    rule: LabelDerivationRule,
    endpoint_month: CalendarMonth,
    transition_interval_months: WindowSpanMonths,
) -> TransitionDisplacement | None:
    windows = transition_windows(endpoint_month, transition_interval_months)
    months, keep = _labeled_months(records, rule, want_malicious=True)
    features = features[keep]
    kept_months = months[keep]
    before_mean, before_support = windowed_mean(
        features,
        kept_months,
        windows.before_window_start_inclusive,
        windows.before_window_end_exclusive,
    )
    after_mean, after_support = windowed_mean(
        features,
        kept_months,
        windows.after_window_start_inclusive,
        windows.after_window_end_exclusive,
    )
    if before_support == 0 or after_support == 0:
        return None
    return TransitionDisplacement(
        displacement=after_mean - before_mean,
        support_before=before_support,
        support_after=after_support,
    )


def windowed_malicious_features(
    records: Sequence[LamdaRawRecord],
    features: np.ndarray,
    rule: LabelDerivationRule,
    endpoint_month: CalendarMonth,
    transition_interval_months: WindowSpanMonths,
) -> tuple[np.ndarray, np.ndarray]:
    windows = transition_windows(endpoint_month, transition_interval_months)
    months, keep = _labeled_months(records, rule, want_malicious=True)
    kept_features = features[keep].astype(np.float64)
    kept_months = months[keep]
    before_mask = (kept_months >= windows.before_window_start_inclusive) & (
        kept_months < windows.before_window_end_exclusive
    )
    after_mask = (kept_months >= windows.after_window_start_inclusive) & (
        kept_months < windows.after_window_end_exclusive
    )
    return kept_features[before_mask], kept_features[after_mask]


def _retained_sample_mask(
    sample_hashes: Sequence[SampleIdentifier],
    cutoff: CalendarMonth,
    retention_fraction: Fraction,
) -> np.ndarray:
    if not sample_hashes:
        return np.zeros(0, dtype=bool)
    digests = [
        hashlib.sha256(f"{sample_hash}:{cutoff}:{retention_fraction}".encode()).hexdigest()
        for sample_hash in sample_hashes
    ]
    retain_count = max(1, round(len(digests) * retention_fraction))
    threshold = sorted(digests)[retain_count - 1]
    return np.fromiter((digest <= threshold for digest in digests), dtype=bool, count=len(digests))


def _sparse_windowed_mean(
    features: np.ndarray,
    months: np.ndarray,
    sample_hashes: np.ndarray,
    start_inclusive: CalendarMonth,
    end_exclusive: CalendarMonth,
    cutoff: CalendarMonth,
    retention_fraction: Fraction,
) -> tuple[np.ndarray, SampleCount]:
    window_mask = (months >= start_inclusive) & (months < end_exclusive)
    window_indices = np.flatnonzero(window_mask)
    if window_indices.size == 0:
        return np.zeros(features.shape[1], dtype=np.float64), 0
    retained = _retained_sample_mask(
        [SampleIdentifier(sample_hashes[index]) for index in window_indices],
        cutoff,
        retention_fraction,
    )
    retained_indices = window_indices[retained]
    if retained_indices.size == 0:
        return np.zeros(features.shape[1], dtype=np.float64), 0
    return (
        features[retained_indices].astype(np.float64).mean(axis=0),
        int(retained_indices.size),
    )


def control_transition_replicates(
    records: Sequence[LamdaRawRecord],
    features: np.ndarray,
    rule: LabelDerivationRule,
    candidate_endpoints: Sequence[CalendarMonth],
    transition_interval_months: WindowSpanMonths,
) -> tuple[ControlTransitionReplicate, ...]:
    months, keep = _labeled_months(records, rule, want_malicious=False)
    features = features[keep]
    kept_months = months[keep]
    replicates: list[ControlTransitionReplicate] = []
    for endpoint in candidate_endpoints:
        windows = transition_windows(endpoint, transition_interval_months)
        before_mean, before_support = windowed_mean(
            features,
            kept_months,
            windows.before_window_start_inclusive,
            windows.before_window_end_exclusive,
        )
        after_mean, after_support = windowed_mean(
            features,
            kept_months,
            windows.after_window_start_inclusive,
            windows.after_window_end_exclusive,
        )
        if before_support == 0 or after_support == 0:
            continue
        replicates.append(
            ControlTransitionReplicate(
                endpoint_month=endpoint,
                displacement=after_mean - before_mean,
                support_before=before_support,
                support_after=after_support,
            )
        )
    return tuple(replicates)


def sparse_control_transition_replicates(
    records: Sequence[LamdaRawRecord],
    features: np.ndarray,
    rule: LabelDerivationRule,
    candidate_endpoints: Sequence[CalendarMonth],
    transition_interval_months: WindowSpanMonths,
    retention_fraction: Fraction,
) -> tuple[ControlTransitionReplicate, ...]:
    months, keep = _labeled_months(records, rule, want_malicious=False)
    kept_records = [record for record, keep_flag in zip(records, keep, strict=True) if keep_flag]
    kept_sample_hashes = np.array([record.sample_hash for record in kept_records])
    kept_features = features[keep]
    kept_months = months[keep]
    replicates: list[ControlTransitionReplicate] = []
    for endpoint in candidate_endpoints:
        windows = transition_windows(endpoint, transition_interval_months)
        before_mean, before_support = _sparse_windowed_mean(
            kept_features,
            kept_months,
            kept_sample_hashes,
            windows.before_window_start_inclusive,
            windows.before_window_end_exclusive,
            endpoint,
            retention_fraction,
        )
        after_mean, after_support = _sparse_windowed_mean(
            kept_features,
            kept_months,
            kept_sample_hashes,
            windows.after_window_start_inclusive,
            windows.after_window_end_exclusive,
            endpoint,
            retention_fraction,
        )
        if before_support == 0 or after_support == 0:
            continue
        replicates.append(
            ControlTransitionReplicate(
                endpoint_month=endpoint,
                displacement=after_mean - before_mean,
                support_before=before_support,
                support_after=after_support,
            )
        )
    return tuple(replicates)


def effective_support(replicate: ControlTransitionReplicate) -> ThresholdValue:
    return 1.0 / (1.0 / replicate.support_before + 1.0 / replicate.support_after)


def replicate_weights(
    replicates: Sequence[ControlTransitionReplicate],
) -> tuple[Probability, ...]:
    supports = [effective_support(replicate) for replicate in replicates]
    total = sum(supports)
    if total <= 0.0:
        return tuple(0.0 for _replicate in replicates)
    return tuple(support / total for support in supports)


def lamda_schema_manifest(
    records: Sequence[LamdaRawRecord], features: np.ndarray
) -> SchemaChronologyManifest:
    sorted_hashes = sorted(record.sample_hash for record in records)
    digest = hashlib.sha256(",".join(sorted_hashes).encode("utf-8")).hexdigest() #TODO: should be enum not hardcoded string
    observed_months = sorted({record.year_month for record in records})
    if observed_months:
        first_month = year_month_to_calendar_month(observed_months[0])
        last_month = year_month_to_calendar_month(observed_months[-1])
    else:
        first_month = calendar_month(0)
        last_month = calendar_month(0)
    return SchemaChronologyManifest(
        dataset=DatasetIdentity(DatasetSelector.LAMDA),
        acquisition_checksum=f"sha256:{digest}", #TODO: should be enums not hardcoded strings
        fields=(
            SchemaManifestField(name="hash", observed=len(records) > 0),
            SchemaManifestField(
                name="label", observed=any(record.label is not None for record in records)
            ),
            SchemaManifestField(
                name="family",
                observed=any(record.family is not None for record in records),
            ),
            SchemaManifestField(
                name="vt_count",
                observed=any(record.vt_count is not None for record in records),
            ),
            SchemaManifestField(name="year_month", observed=len(observed_months) > 0),
        ),
        observed_row_count=len(records),
        observed_feature_dimension=features.shape[1] if features.ndim == 2 else None,
        chronology_granularity="year_month",
        first_observed_month=int(first_month),
        last_observed_month=int(last_month),
    )


class LamdaValidationError(ValueError):
    pass


def validate_lamda_dataset(dataset: LoadedLamdaDataset) -> None:
    if len(dataset.records) != dataset.features.shape[0]:
        raise LamdaValidationError("record count and feature rows must match")
