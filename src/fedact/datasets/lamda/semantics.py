from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import NewType

import numpy as np

from fedact.config.models import LamdaDatasetConfig
from fedact.datasets.chronology import CalendarMonth, calendar_month, transition_windows
from fedact.datasets.records import (
    ClientSemanticsAudit,
    LabelDerivationRule,
    corpus_level_client_audit,
)
from fedact.domain.enums import DatasetSelector
from fedact.domain.records import SampleIdentifier
from fedact.domain.types import BinaryLabel, CalendarMonthString, FamilyName, SampleCount

_LAMDA_EPOCH_YEAR = 2013


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


def _expected_label(rule: LabelDerivationRule, vt_count: SampleCount) -> bool | None:
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
    controls_by_month: dict[str, list[LamdaRawRecord]] = {}
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
    has_matching_raw_artifact: bool

    def is_eligible(self) -> bool:
        return self.has_matching_raw_artifact


def year_month_to_calendar_month(year_month: CalendarMonthString) -> CalendarMonth:
    year_text, month_text = year_month.split("-")
    ordinal = (int(year_text) - _LAMDA_EPOCH_YEAR) * 12 + (int(month_text) - 1)
    return calendar_month(ordinal)


@dataclass(frozen=True)
class TransitionDisplacement:
    displacement: np.ndarray
    support_before: SampleCount
    support_after: SampleCount


@dataclass(frozen=True)
class ControlTransitionReplicate:
    endpoint_month: CalendarMonth
    displacement: np.ndarray
    support_before: SampleCount
    support_after: SampleCount


def _windowed_mean(
    features: np.ndarray,
    months: np.ndarray,
    start_inclusive: CalendarMonth,
    end_exclusive: CalendarMonth,
) -> tuple[np.ndarray, SampleCount]:
    mask = (months >= start_inclusive) & (months < end_exclusive)
    support = int(mask.sum())
    if support == 0:
        return np.zeros(features.shape[1], dtype=np.float64), 0
    return features[mask].astype(np.float64).mean(axis=0), support


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
    transition_interval_months: int,
) -> TransitionDisplacement | None:
    windows = transition_windows(endpoint_month, transition_interval_months)
    months, keep = _labeled_months(records, rule, want_malicious=True)
    features = features[keep]
    kept_months = months[keep]
    before_mean, before_support = _windowed_mean(
        features, kept_months, windows.before_window_start_inclusive, windows.before_window_end_exclusive
    )
    after_mean, after_support = _windowed_mean(
        features, kept_months, windows.after_window_start_inclusive, windows.after_window_end_exclusive
    )
    if before_support == 0 or after_support == 0:
        return None
    return TransitionDisplacement(
        displacement=after_mean - before_mean,
        support_before=before_support,
        support_after=after_support,
    )


def control_transition_replicates(
    records: Sequence[LamdaRawRecord],
    features: np.ndarray,
    rule: LabelDerivationRule,
    candidate_endpoints: Sequence[CalendarMonth],
    transition_interval_months: int,
) -> tuple[ControlTransitionReplicate, ...]:
    months, keep = _labeled_months(records, rule, want_malicious=False)
    features = features[keep]
    kept_months = months[keep]
    replicates: list[ControlTransitionReplicate] = []
    for endpoint in candidate_endpoints:
        windows = transition_windows(endpoint, transition_interval_months)
        before_mean, before_support = _windowed_mean(
            features,
            kept_months,
            windows.before_window_start_inclusive,
            windows.before_window_end_exclusive,
        )
        after_mean, after_support = _windowed_mean(
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


def effective_support(replicate: ControlTransitionReplicate) -> float:
    return 1.0 / (1.0 / replicate.support_before + 1.0 / replicate.support_after)


def replicate_weights(replicates: Sequence[ControlTransitionReplicate]) -> tuple[float, ...]:
    supports = [effective_support(replicate) for replicate in replicates]
    total = sum(supports)
    if total <= 0.0:
        return tuple(0.0 for _ in replicates)
    return tuple(support / total for support in supports)
