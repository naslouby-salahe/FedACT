from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

from pydantic import Field

from fedact.config.models import NonNegativeInt, PositiveInt
from fedact.domain.enums import DatasetSelector
from fedact.domain.records import DatasetIdentity, SplitCutoffIdentity
from fedact.domain.types import (
    CalendarMonthString,
    CohortIdentifier,
    DetailMessage,
    DimensionValue,
    FieldName,
    HashDigest,
    MaliciousnessFlag,
    MonthIndex,
    SampleCount,
    ValidationFlag,
    WindowMonth,
)


class ExclusionReason(StrEnum):
    CONFLICTING_DUPLICATE = "CONFLICTING_DUPLICATE"
    MALFORMED_RECORD = "MALFORMED_RECORD"
    NONFINITE_FEATURE = "NONFINITE_FEATURE"
    MISSING_SAMPLE_IDENTITY = "MISSING_SAMPLE_IDENTITY"
    MISSING_CHRONOLOGY = "MISSING_CHRONOLOGY"
    MISSING_BINARY_LABEL = "MISSING_BINARY_LABEL"
    LABEL_VT_COUNT_CONFLICT = "LABEL_VT_COUNT_CONFLICT"
    LOW_VARIANCE_FEATURE = "LOW_VARIANCE_FEATURE"
    VALIDATION_STRATUM_TOO_SMALL = "VALIDATION_STRATUM_TOO_SMALL"


class EligibilityStatus(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    OPERATOR_INELIGIBLE = "operator_ineligible"


class ClientSemanticsClass(StrEnum):
    NATURAL_ORGANIZATION = "natural-organization"
    NATURAL_SOURCE = "natural-source"
    DIAGNOSTIC_PARTITION = "diagnostic-partition"
    CORPUS_LEVEL_CLIENT = "corpus-level-client"


class DatasetEligibilityRole(StrEnum):
    PRIMARY_EVIDENCE = "eligible-for-primary-evidence"
    SECONDARY_EVIDENCE = "eligible-for-secondary-evidence"
    DIAGNOSTIC_ONLY = "diagnostic-only"
    UNUSABLE = "unusable-for-the-intended-evidence"


class FeasibilityCondition(StrEnum):
    CHRONOLOGY_VALID = "chronology-valid"
    MALICIOUS_HISTORY_SUFFICIENT = "malicious-history-sufficient"
    CONTROLS_SUFFICIENT = "controls-sufficient"
    CONTEXT_FIELDS_OBSERVED = "required-context-fields-observed"
    COHORTS_CUTOFF_SAFE = "cohorts-cutoff-safe"
    OPERATOR_ARTIFACTS_AVAILABLE = "raw-operator-artifacts-available"
    REPRESENTATION_TRAINABLE_WITHOUT_LEAKAGE = "representation-trainable-without-leakage"


FEASIBILITY_CONDITION_ORDER: tuple[FeasibilityCondition, ...] = (
    FeasibilityCondition.CHRONOLOGY_VALID,
    FeasibilityCondition.MALICIOUS_HISTORY_SUFFICIENT,
    FeasibilityCondition.CONTROLS_SUFFICIENT,
    FeasibilityCondition.CONTEXT_FIELDS_OBSERVED,
    FeasibilityCondition.COHORTS_CUTOFF_SAFE,
    FeasibilityCondition.OPERATOR_ARTIFACTS_AVAILABLE,
    FeasibilityCondition.REPRESENTATION_TRAINABLE_WITHOUT_LEAKAGE,
)


class LabelDerivationRuleError(ValueError):
    pass


@dataclass(frozen=True)
class LabelDerivationRule:
    benign_detection_count: NonNegativeInt
    malware_minimum_detection_count: PositiveInt
    discard_detection_counts: tuple[NonNegativeInt, ...]


VirusTotalDetectionCount = Annotated[int, Field(ge=0)]


def is_derived_label_malicious(
    rule: LabelDerivationRule, vt_detection_count: VirusTotalDetectionCount
) -> MaliciousnessFlag:
    if vt_detection_count == rule.benign_detection_count:
        return False
    if vt_detection_count >= rule.malware_minimum_detection_count:
        return True
    if vt_detection_count in rule.discard_detection_counts:
        raise LabelDerivationRuleError(
            f"vt_count {vt_detection_count} falls in the discard band and yields no binary label"
        )
    raise LabelDerivationRuleError(
        f"vt_count {vt_detection_count} is outside the roadmap label-derivation rule bands"
    )


@dataclass(frozen=True)
class SchemaManifestField:
    name: FieldName
    observed: ValidationFlag


@dataclass(frozen=True)
class SchemaChronologyManifest:
    dataset: DatasetIdentity
    acquisition_checksum: HashDigest
    fields: tuple[SchemaManifestField, ...]
    observed_row_count: SampleCount
    observed_feature_dimension: DimensionValue | None
    chronology_granularity: CalendarMonthString
    first_observed_month: MonthIndex
    last_observed_month: MonthIndex

    def __post_init__(self) -> None:
        if self.observed_row_count < 0:
            raise ValueError("observed row count must be nonnegative")
        if self.last_observed_month < self.first_observed_month:
            raise ValueError(
                "schema manifest last observed month precedes its first observed month"
            )


@dataclass(frozen=True)
class ExclusionRecord:
    dataset: DatasetSelector
    cutoff_identity: SplitCutoffIdentity
    reason: ExclusionReason
    excluded_count: SampleCount


@dataclass(frozen=True)
class CohortRecord:
    cohort_id: CohortIdentifier
    definition: DetailMessage
    availability_timestamp: CalendarMonthString
    dataset_id: DatasetIdentity
    client_id: DetailMessage
    support_count: SampleCount
    window_start: WindowMonth
    window_end: WindowMonth
    eligibility_status: EligibilityStatus


@dataclass(frozen=True)
class ClientSemanticsAudit:
    dataset: DatasetSelector
    source_field: FieldName
    classification: ClientSemanticsClass
    observed_values: tuple[str, ...]
    supports_natural_federation_claim: ValidationFlag

    def __post_init__(self) -> None:
        strong = self.classification in (
            ClientSemanticsClass.NATURAL_ORGANIZATION,
            ClientSemanticsClass.NATURAL_SOURCE,
        )
        if self.supports_natural_federation_claim and not strong:
            raise ValueError(
                "only natural organization or natural source identities may support a "
                "strong natural-federation claim"
            )


def corpus_level_client_audit(dataset: DatasetSelector) -> ClientSemanticsAudit:
    return ClientSemanticsAudit(
        dataset=dataset,
        source_field="none",
        classification=ClientSemanticsClass.CORPUS_LEVEL_CLIENT,
        observed_values=(dataset.value,),
        supports_natural_federation_claim=False,
    )


@dataclass(frozen=True)
class DatasetEligibilityOutcome:
    dataset: DatasetSelector
    satisfied_conditions: frozenset[FeasibilityCondition]
    failed_conditions: frozenset[FeasibilityCondition]

    @property
    def role(self) -> DatasetEligibilityRole:
        if self.failed_conditions == frozenset():
            return DatasetEligibilityRole.PRIMARY_EVIDENCE
        if FeasibilityCondition.CHRONOLOGY_VALID in self.failed_conditions:
            return DatasetEligibilityRole.UNUSABLE
        if self.failed_conditions <= {
            FeasibilityCondition.OPERATOR_ARTIFACTS_AVAILABLE,
            FeasibilityCondition.COHORTS_CUTOFF_SAFE,
        }:
            return DatasetEligibilityRole.SECONDARY_EVIDENCE
        return DatasetEligibilityRole.DIAGNOSTIC_ONLY
