from __future__ import annotations

from dataclasses import dataclass

from fedact.datasets.chronology import CalendarMonth, SourceChronology
from fedact.datasets.records import (
    ClientSemanticsAudit,
    DatasetEligibilityOutcome,
    FeasibilityCondition,
    SchemaChronologyManifest,
)
from fedact.domain.enums import DatasetSelector
from fedact.domain.records import (
    OverlapFlag,
    PassingFlag,
    SampleCount,
    SplitCutoffIdentity,
    ValidationFlag,
)


class AuditContractError(ValueError):
    pass


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


@dataclass(frozen=True)
class SupportAuditResult:
    malicious_count: SampleCount
    control_count: SampleCount
    control_strata_count: SampleCount
    operator_eligible_count: SampleCount

    def has_temporal_overlap_with(self, other: SupportAuditResult) -> OverlapFlag:
        return self.malicious_count > 0 and other.malicious_count > 0


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


def run_feasibility_audit(
    chronology: ChronologyAuditResult,
    client_semantics: ClientSemanticsAudit,
    schema_manifest: SchemaChronologyManifest,
) -> DatasetEligibilityOutcome:
    if not chronology.is_passing:
        return DatasetEligibilityOutcome(
            dataset=chronology.dataset,
            satisfied_conditions=frozenset(),
            failed_conditions=frozenset({FeasibilityCondition.CHRONOLOGY_VALID}),
        )
    satisfied = {
        FeasibilityCondition.CHRONOLOGY_VALID,
        FeasibilityCondition.CONTEXT_FIELDS_OBSERVED,
        FeasibilityCondition.REPRESENTATION_TRAINABLE_WITHOUT_LEAKAGE,
    }
    if schema_manifest.observed_row_count > 0:
        satisfied.add(FeasibilityCondition.MALICIOUS_HISTORY_SUFFICIENT)
    if client_semantics.source_field != "none":
        satisfied.add(FeasibilityCondition.CONTROLS_SUFFICIENT)
    return DatasetEligibilityOutcome(
        dataset=chronology.dataset,
        satisfied_conditions=frozenset(satisfied),
        failed_conditions=frozenset(set(FeasibilityCondition) - satisfied),
    )
