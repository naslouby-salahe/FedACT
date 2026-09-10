from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import NewType

from fedact.domain.types import (
    DatasetSelector,
    EligibilityFlag,
    EligibilityStatus,
    HorizonAvailability,
    HorizonMonths,
    MonthIndex,
    ObservabilityFlag,
    OverlapFlag,
    PairedCutoffCount,
    PassingFlag,
    SampleCount,
    SampleIdentifier,
    ScientificOutcome,
    SplitCutoffIdentity,
    SufficiencyFlag,
    SupportThreshold,
    ValidationFlag,
    WindowSpanMonths,
)

CalendarMonth = NewType("CalendarMonth", int)

_TRANSITION_WINDOW_SPAN_MULTIPLIER = 2


def calendar_month(value: MonthIndex) -> CalendarMonth:
    if value < 0:
        raise ChronologyError(f"calendar month must be nonnegative; got {value}")
    return CalendarMonth(value)


class ChronologyError(ValueError):
    pass


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
    ) -> ObservabilityFlag:
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


DATASET_SOURCE_CHRONOLOGY: dict[DatasetSelector, SourceChronology] = {
    DatasetSelector.LAMDA: SourceChronology(
        first_observed_month=calendar_month(0),
        last_observed_month=calendar_month(144),
        prohibited_gaps=(LAMDA_MISSING_2015_GAP,),
    ),
    DatasetSelector.EMBER2024: SourceChronology(
        first_observed_month=calendar_month(0),
        last_observed_month=calendar_month(14),
    ),
}


def dataset_source_chronology(dataset: DatasetSelector) -> SourceChronology:
    return DATASET_SOURCE_CHRONOLOGY[dataset]


def is_interval_overlapping_gap(
    start_inclusive: CalendarMonth, end_exclusive: CalendarMonth, gap: SourceGap
) -> OverlapFlag:
    return (
        start_inclusive <= gap.gap_start_exclusive_month
        and gap.gap_end_inclusive_month < end_exclusive
    ) or (
        gap.gap_start_exclusive_month < end_exclusive
        and start_inclusive <= gap.gap_end_inclusive_month
    )


def month_offset(base: CalendarMonth, months: WindowSpanMonths) -> CalendarMonth:
    return CalendarMonth(base + months)


@dataclass(frozen=True)
class TransitionWindows:
    endpoint_month: CalendarMonth
    before_window_start_inclusive: CalendarMonth
    before_window_end_exclusive: CalendarMonth
    after_window_start_inclusive: CalendarMonth
    after_window_end_exclusive: CalendarMonth


def earliest_complete_transition_endpoint(
    origin_month: CalendarMonth, transition_interval_months: WindowSpanMonths
) -> CalendarMonth:
    return CalendarMonth(
        origin_month + _TRANSITION_WINDOW_SPAN_MULTIPLIER * transition_interval_months
    )


def transition_windows(
    endpoint_month: CalendarMonth, transition_interval_months: WindowSpanMonths
) -> TransitionWindows:
    if endpoint_month < _TRANSITION_WINDOW_SPAN_MULTIPLIER * transition_interval_months:
        raise ChronologyError(
            "transition endpoint precedes the start of two complete transition windows"
        )
    return TransitionWindows(
        endpoint_month=endpoint_month,
        before_window_start_inclusive=CalendarMonth(
            endpoint_month - _TRANSITION_WINDOW_SPAN_MULTIPLIER * transition_interval_months
        ),
        before_window_end_exclusive=CalendarMonth(endpoint_month - transition_interval_months),
        after_window_start_inclusive=CalendarMonth(endpoint_month - transition_interval_months),
        after_window_end_exclusive=endpoint_month,
    )


def is_endpoint_eligible_for_cutoff(
    endpoint_month: CalendarMonth,
    cutoff_exclusive_month: CalendarMonth,
    historical_training_window_months: WindowSpanMonths,
) -> EligibilityFlag:
    historical_start = cutoff_exclusive_month - historical_training_window_months
    return historical_start <= endpoint_month < cutoff_exclusive_month


def enumerate_historical_endpoints(
    source: SourceChronology,
    cutoff_exclusive_month: CalendarMonth,
    historical_training_window_months: WindowSpanMonths,
    transition_interval_months: WindowSpanMonths,
    cutoff_step_months: WindowSpanMonths,
) -> tuple[CalendarMonth, ...]:
    history_start = cutoff_exclusive_month - historical_training_window_months
    endpoints: list[CalendarMonth] = []
    step = cutoff_step_months
    earliest_complete = earliest_complete_transition_endpoint(
        CalendarMonth(history_start), transition_interval_months
    )
    floor_from_origin = earliest_complete_transition_endpoint(
        CalendarMonth(0), transition_interval_months
    )
    candidate = max(earliest_complete, floor_from_origin)
    if step > 1:
        candidate = ((candidate + step - 1) // step) * step
    while candidate < cutoff_exclusive_month:
        windows = transition_windows(CalendarMonth(candidate), transition_interval_months)
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
    historical_training_window_months: WindowSpanMonths,
    primary_confirmatory_horizon_months: HorizonMonths,
    cutoff_step_months: WindowSpanMonths,
) -> tuple[EligibleCutoff, ...]:
    eligible: list[EligibleCutoff] = []
    first_candidate = source.first_observed_month + historical_training_window_months
    last_candidate = source.last_observed_month + 1
    candidate = first_candidate
    while candidate <= last_candidate:
        history_start = candidate - historical_training_window_months
        if source.is_interval_observable(CalendarMonth(history_start), CalendarMonth(candidate)):
            identity = SplitCutoffIdentity(f"month-{candidate:06d}")
            horizon_end = month_offset(
                CalendarMonth(candidate), primary_confirmatory_horizon_months
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
        candidate += cutoff_step_months
    return tuple(eligible)


@dataclass(frozen=True)
class HorizonEvaluation:
    horizon_months: HorizonMonths
    availability: HorizonAvailability


def classify_horizon_availability(
    source: SourceChronology,
    cutoff_exclusive_month: CalendarMonth,
    horizons: tuple[HorizonMonths, ...],
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


def confirmatory_outcome_for_cutoffs(
    eligible_pair_count: PairedCutoffCount, minimum_paired_cutoffs: PairedCutoffCount
) -> ScientificOutcome:
    if eligible_pair_count < minimum_paired_cutoffs:
        return ScientificOutcome.INSUFFICIENT_EVIDENCE
    return ScientificOutcome.PASS


def reuse_source_checkpoint_month(
    cutoff_exclusive_month: CalendarMonth, full_retraining_interval_months: WindowSpanMonths
) -> CalendarMonth:
    if cutoff_exclusive_month % full_retraining_interval_months == 0:
        return cutoff_exclusive_month
    completed_intervals = cutoff_exclusive_month // full_retraining_interval_months
    if completed_intervals == 0:
        raise ChronologyError(
            "no compatible earlier retraining checkpoint exists for this intermediate cutoff"
        )
    return CalendarMonth(completed_intervals * full_retraining_interval_months)


class SplitPartition(StrEnum):
    TRAINING = "training"
    VALIDATION = "validation"
    TEST = "test"


class SplitConstructionError(ValueError):
    pass


IndexInPopulation = NewType("IndexInPopulation", int)


@dataclass(frozen=True)
class SplitAssignment:
    sample_id: SampleIdentifier
    cutoff_identity: SplitCutoffIdentity
    partition: SplitPartition
    eligibility_status: EligibilityStatus


@dataclass(frozen=True)
class PartitionCounts:
    training: SampleCount
    validation: SampleCount
    test: SampleCount

    def for_partition(self, partition: SplitPartition) -> SampleCount:
        if partition is SplitPartition.TRAINING:
            return self.training
        if partition is SplitPartition.VALIDATION:
            return self.validation
        return self.test


@dataclass(frozen=True)
class CutoffSplit:
    cutoff_identity: SplitCutoffIdentity
    assignments: tuple[SplitAssignment, ...]

    def partition_counts(self) -> PartitionCounts:
        training = sum(
            1 for assignment in self.assignments if assignment.partition is SplitPartition.TRAINING
        )
        validation = sum(
            1
            for assignment in self.assignments
            if assignment.partition is SplitPartition.VALIDATION
        )
        test = sum(
            1 for assignment in self.assignments if assignment.partition is SplitPartition.TEST
        )
        return PartitionCounts(training=training, validation=validation, test=test)

    def operator_eligible_ids(self) -> tuple[SampleIdentifier, ...]:
        return tuple(
            assignment.sample_id
            for assignment in self.assignments
            if assignment.eligibility_status is EligibilityStatus.ELIGIBLE
        )


def construct_cutoff_split(
    cutoff_identity: SplitCutoffIdentity,
    sample_ids: tuple[SampleIdentifier, ...],
    training_indices: frozenset[IndexInPopulation],
    validation_indices: frozenset[IndexInPopulation],
    test_indices: frozenset[IndexInPopulation],
    operator_eligible: frozenset[SampleIdentifier],
) -> CutoffSplit:
    if training_indices & validation_indices or training_indices & test_indices:
        raise SplitConstructionError(
            "cutoff-safe split partitions must be disjoint; leakage boundary violated"
        )
    if validation_indices & test_indices:
        raise SplitConstructionError(
            "cutoff-safe split partitions must be disjoint; leakage boundary violated"
        )
    covered = training_indices | validation_indices | test_indices
    if any(index < 0 or index >= len(sample_ids) for index in covered):
        raise SplitConstructionError("split index outside the sample population")
    assignments: list[SplitAssignment] = []
    for index, sample_id in enumerate(sample_ids):
        position = IndexInPopulation(index)
        if position in training_indices:
            partition = SplitPartition.TRAINING
        elif position in validation_indices:
            partition = SplitPartition.VALIDATION
        elif position in test_indices:
            partition = SplitPartition.TEST
        else:
            continue
        status = (
            EligibilityStatus.ELIGIBLE
            if sample_id in operator_eligible
            else EligibilityStatus.OPERATOR_INELIGIBLE
        )
        assignments.append(
            SplitAssignment(
                sample_id=sample_id,
                cutoff_identity=cutoff_identity,
                partition=partition,
                eligibility_status=status,
            )
        )
    return CutoffSplit(cutoff_identity=cutoff_identity, assignments=tuple(assignments))


def is_meeting_support_floor(
    counts: SampleCount, minimum_support_per_class: SupportThreshold
) -> SufficiencyFlag:
    return counts >= minimum_support_per_class


@dataclass(frozen=True)
class ChronologyAuditResult:
    dataset: DatasetSelector
    cutoff_identity: SplitCutoffIdentity
    source_observable_history: ValidationFlag
    no_future_derived_labels_used: ValidationFlag
    ordering_complete: ValidationFlag

    @property
    def is_passing(self) -> PassingFlag:
        return (
            self.source_observable_history
            and self.no_future_derived_labels_used
            and self.ordering_complete
        )


def audit_chronology(
    dataset: DatasetSelector,
    cutoff_identity: SplitCutoffIdentity,
    source: SourceChronology,
    history_start_month: CalendarMonth,
    cutoff_exclusive_end_month: CalendarMonth,
) -> ChronologyAuditResult:
    observable = source.is_interval_observable(history_start_month, cutoff_exclusive_end_month)
    return ChronologyAuditResult(
        dataset=dataset,
        cutoff_identity=cutoff_identity,
        source_observable_history=observable,
        no_future_derived_labels_used=observable,
        ordering_complete=cutoff_exclusive_end_month > history_start_month,
    )
