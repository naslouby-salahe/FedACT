from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, NewType

from pydantic import Field

from fedact.config.models import FedActConfig, PositiveInt
from fedact.domain.enums import ScientificOutcome
from fedact.domain.records import SplitCutoffIdentity
from fedact.domain.types import (
    ValidationFlag,
)

CalendarMonth = NewType("CalendarMonth", int)


def calendar_month(value: int) -> CalendarMonth:
    if value < 0:
        raise ChronologyError(f"calendar month must be nonnegative; got {value}")
    return CalendarMonth(value)


class ChronologyError(ValueError):
    pass


class HorizonAvailability(StrEnum):
    OBSERVABLE = "OBSERVABLE"
    MISSING_SOURCE_DATA = "MISSING_SOURCE_DATA"


@dataclass(frozen=True)
class SourceGap:
    gap_start_exclusive_month: CalendarMonth
    gap_end_inclusive_month: CalendarMonth


LAMDA_MISSING_2015_GAP = SourceGap(
    gap_start_exclusive_month=calendar_month(24),
    gap_end_inclusive_month=calendar_month(35),
)


@dataclass(frozen=True)
class SourceChronology:
    first_observed_month: CalendarMonth
    last_observed_month: CalendarMonth
    prohibited_gaps: tuple[SourceGap, ...] = ()

    def __post_init__(self) -> None:
        if self.last_observed_month < self.first_observed_month:
            raise ChronologyError(
                "source chronology last observed month precedes its first observed month"
            )

    def is_interval_observable(
        self, start_inclusive: CalendarMonth, end_exclusive: CalendarMonth
    ) -> bool:
        if start_inclusive >= end_exclusive:
            raise ChronologyError("observability intervals must be non-empty and half-open")
        if start_inclusive < self.first_observed_month:
            return False
        if end_exclusive - 1 > self.last_observed_month:
            return False
        return not any(
            is_interval_overlapping_gap(start_inclusive, end_exclusive, gap)
            for gap in self.prohibited_gaps
        )


def is_interval_overlapping_gap(
    start_inclusive: CalendarMonth, end_exclusive: CalendarMonth, gap: SourceGap
) -> bool:
    return (
        start_inclusive <= gap.gap_start_exclusive_month
        and gap.gap_end_inclusive_month < end_exclusive
    ) or (
        gap.gap_start_exclusive_month < end_exclusive
        and start_inclusive <= gap.gap_end_inclusive_month
    )


def month_offset(base: CalendarMonth, months: PositiveInt) -> CalendarMonth:
    return CalendarMonth(base + months)


@dataclass(frozen=True)
class TransitionWindows:
    endpoint_month: CalendarMonth
    before_window_start_inclusive: CalendarMonth
    before_window_end_exclusive: CalendarMonth
    after_window_start_inclusive: CalendarMonth
    after_window_end_exclusive: CalendarMonth


def transition_windows(
    endpoint_month: CalendarMonth, transition_interval_months: PositiveInt
) -> TransitionWindows:
    if endpoint_month < 2 * transition_interval_months:
        raise ChronologyError(
            "transition endpoint precedes the start of two complete transition windows"
        )
    return TransitionWindows(
        endpoint_month=endpoint_month,
        before_window_start_inclusive=CalendarMonth(
            endpoint_month - 2 * transition_interval_months
        ),
        before_window_end_exclusive=CalendarMonth(endpoint_month - transition_interval_months),
        after_window_start_inclusive=CalendarMonth(endpoint_month - transition_interval_months),
        after_window_end_exclusive=endpoint_month,
    )


def is_endpoint_eligible_for_cutoff(
    endpoint_month: CalendarMonth,
    cutoff_exclusive_month: CalendarMonth,
    historical_training_window_months: PositiveInt,
) -> bool:
    historical_start = cutoff_exclusive_month - historical_training_window_months
    return historical_start <= endpoint_month < cutoff_exclusive_month


def enumerate_historical_endpoints(
    source: SourceChronology,
    cutoff_exclusive_month: CalendarMonth,
    config: FedActConfig,
) -> tuple[CalendarMonth, ...]:
    temporal = config.temporal
    history_start = cutoff_exclusive_month - temporal.historical_training_window_months
    endpoints: list[CalendarMonth] = []
    step = temporal.cutoff_step_months
    earliest_complete = history_start + 2 * temporal.transition_interval_months
    floor_from_origin = 2 * temporal.transition_interval_months
    candidate = max(earliest_complete, floor_from_origin)
    if step > 1:
        candidate = ((candidate + step - 1) // step) * step
    while candidate < cutoff_exclusive_month:
        windows = transition_windows(CalendarMonth(candidate), temporal.transition_interval_months)
        if source.is_interval_observable(
            windows.before_window_start_inclusive, CalendarMonth(candidate)
        ):
            endpoints.append(CalendarMonth(candidate))
        candidate += step
    return tuple(endpoints)


@dataclass(frozen=True)
class EligibleCutoff:
    cutoff_identity: SplitCutoffIdentity
    cutoff_exclusive_month: CalendarMonth
    primary_confirmatory: ValidationFlag


def enumerate_rolling_cutoffs(
    source: SourceChronology,
    config: FedActConfig,
) -> tuple[EligibleCutoff, ...]:
    temporal = config.temporal
    eligible: list[EligibleCutoff] = []
    first_candidate = source.first_observed_month + temporal.historical_training_window_months
    last_candidate = source.last_observed_month + 1
    candidate = first_candidate
    while candidate <= last_candidate:
        history_start = candidate - temporal.historical_training_window_months
        if source.is_interval_observable(CalendarMonth(history_start), CalendarMonth(candidate)):
            identity = SplitCutoffIdentity(f"month-{candidate:06d}")
            horizon_end = month_offset(
                CalendarMonth(candidate), temporal.primary_confirmatory_horizon_months
            )
            eligible.append(
                EligibleCutoff(
                    cutoff_identity=identity,
                    cutoff_exclusive_month=CalendarMonth(candidate),
                    primary_confirmatory=source.is_interval_observable(
                        CalendarMonth(candidate), horizon_end
                    ),
                )
            )
        candidate += temporal.cutoff_step_months
    return tuple(eligible)


@dataclass(frozen=True)
class HorizonEvaluation:
    horizon_months: PositiveInt
    availability: HorizonAvailability


def classify_horizon_availability(
    source: SourceChronology,
    cutoff_exclusive_month: CalendarMonth,
    horizons: tuple[PositiveInt, ...],
) -> tuple[HorizonEvaluation, ...]:
    evaluations: list[HorizonEvaluation] = []
    seen: set[int] = set()
    for horizon in sorted(horizons):
        if horizon in seen:
            raise ChronologyError(f"forecast horizon {horizon} is configured more than once")
        seen.add(horizon)
        observable = source.is_interval_observable(
            cutoff_exclusive_month,
            month_offset(cutoff_exclusive_month, horizon),
        )
        evaluations.append(
            HorizonEvaluation(
                horizon_months=horizon,
                availability=(
                    HorizonAvailability.OBSERVABLE
                    if observable
                    else HorizonAvailability.MISSING_SOURCE_DATA
                ),
            )
        )
    return tuple(evaluations)


PairedCutoffCount = Annotated[int, Field(ge=0)]


def confirmatory_outcome_for_cutoffs(
    eligible_pair_count: PairedCutoffCount, minimum_paired_cutoffs: PositiveInt
) -> ScientificOutcome:
    if eligible_pair_count < minimum_paired_cutoffs:
        return ScientificOutcome.INSUFFICIENT_EVIDENCE
    return ScientificOutcome.PASS


def reuse_source_checkpoint_month(
    cutoff_exclusive_month: CalendarMonth, full_retraining_interval_months: PositiveInt
) -> CalendarMonth:
    if cutoff_exclusive_month % full_retraining_interval_months == 0:
        return cutoff_exclusive_month
    completed_intervals = cutoff_exclusive_month // full_retraining_interval_months
    if completed_intervals == 0:
        raise ChronologyError(
            "no compatible earlier retraining checkpoint exists for this intermediate cutoff"
        )
    return CalendarMonth(completed_intervals * full_retraining_interval_months)
