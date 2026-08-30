from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from fedact.datasets.chronology import CalendarMonth, calendar_month, transition_windows
from fedact.datasets.lamda.loader import LoadedLamdaDataset
from fedact.datasets.lamda.semantics import audited_label
from fedact.datasets.records import LabelDerivationRule
from fedact.domain.types import CalendarMonthString, SampleCount

_LAMDA_EPOCH_YEAR = 2013


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
    dataset: LoadedLamdaDataset,
    rule: LabelDerivationRule,
    want_malicious: bool,
) -> tuple[np.ndarray, np.ndarray]:
    months = np.fromiter(
        (int(year_month_to_calendar_month(record.year_month)) for record in dataset.records),
        dtype=np.int64,
        count=len(dataset.records),
    )
    keep = np.fromiter(
        (
            audited_label(rule, record).binary_label is want_malicious
            for record in dataset.records
        ),
        dtype=bool,
        count=len(dataset.records),
    )
    return months, keep


def malicious_transition_displacement(
    dataset: LoadedLamdaDataset,
    rule: LabelDerivationRule,
    endpoint_month: CalendarMonth,
    transition_interval_months: int,
) -> TransitionDisplacement | None:
    windows = transition_windows(endpoint_month, transition_interval_months)
    months, keep = _labeled_months(dataset, rule, want_malicious=True)
    features = dataset.features[keep]
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
    dataset: LoadedLamdaDataset,
    rule: LabelDerivationRule,
    candidate_endpoints: Sequence[CalendarMonth],
    transition_interval_months: int,
) -> tuple[ControlTransitionReplicate, ...]:
    months, keep = _labeled_months(dataset, rule, want_malicious=False)
    features = dataset.features[keep]
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
