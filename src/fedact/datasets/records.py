from __future__ import annotations

import math
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, NewType

from pydantic import Field

from fedact.config.models import NonNegativeInt, PositiveFloat, PositiveInt
from fedact.datasets.chronology import HorizonAvailability
from fedact.domain.enums import DatasetSelector
from fedact.domain.records import (
    BinaryLabel,
    CalendarMonthString,
    CohortIdentifier,
    ConfirmatoryFlag,
    DatasetIdentity,
    DetailMessage,
    DimensionValue,
    FamilyName,
    FieldName,
    HashDigest,
    MaliciousnessFlag,
    MonthIndex,
    ProhibitionFlag,
    SampleCount,
    SampleIdentifier,
    SplitCutoffIdentity,
    SufficiencyFlag,
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


FeatureValue = NewType("FeatureValue", float)
SupportCount = Annotated[int, Field(ge=0)]
FeatureColumnIndex = NewType("FeatureColumnIndex", int)


class PreprocessingRuleError(ValueError):
    pass


@dataclass(frozen=True)
class PreparedSample:
    sample_id: SampleIdentifier
    month_index: MonthIndex
    label: BinaryLabel | None
    family: FamilyName | None
    features: tuple[FeatureValue, ...]


@dataclass(frozen=True)
class PreparationOutcome:
    retained: tuple[PreparedSample, ...]
    exclusions: tuple[ExclusionRecord, ...]

    def exclusion_count(self, reason: ExclusionReason) -> SampleCount:
        return sum(record.excluded_count for record in self.exclusions if record.reason is reason)


def source_priority_key(sample_id: SampleIdentifier) -> SampleIdentifier:
    return sample_id


def prepare_records(
    dataset: DatasetSelector,
    cutoff_identity: SplitCutoffIdentity,
    records: tuple[PreparedSample, ...],
) -> PreparationOutcome:
    retained_by_id: dict[SampleIdentifier, list[PreparedSample]] = {}
    for record in records:
        if not record.sample_id:
            continue
        retained_by_id.setdefault(record.sample_id, []).append(record)
    exclusions: list[ExclusionRecord] = []
    retained: list[PreparedSample] = []
    conflicting_ids = 0
    for group in retained_by_id.values():
        if len(group) > 1 and any(other != group[0] for other in group[1:]):
            conflicting_ids += 1
            continue
        winner = min(group, key=lambda item: source_priority_key(item.sample_id))
        retained.append(winner)
    if conflicting_ids:
        exclusions.append(
            ExclusionRecord(
                dataset=dataset,
                cutoff_identity=cutoff_identity,
                reason=ExclusionReason.CONFLICTING_DUPLICATE,
                excluded_count=conflicting_ids,
            )
        )

    malformed = sum(1 for record in records if not record.sample_id)
    if malformed:
        exclusions.append(
            ExclusionRecord(
                dataset=dataset,
                cutoff_identity=cutoff_identity,
                reason=ExclusionReason.MISSING_SAMPLE_IDENTITY,
                excluded_count=malformed,
            )
        )

    nonfinite = [
        record for record in retained if any(not math.isfinite(value) for value in record.features)
    ]
    if nonfinite:
        exclusions.append(
            ExclusionRecord(
                dataset=dataset,
                cutoff_identity=cutoff_identity,
                reason=ExclusionReason.NONFINITE_FEATURE,
                excluded_count=len(nonfinite),
            )
        )
        excluded_ids = {record.sample_id for record in nonfinite}
        retained = [record for record in retained if record.sample_id not in excluded_ids]

    missing_chronology_or_label = [
        record for record in retained if record.month_index < 0 or record.label is None
    ]
    if missing_chronology_or_label:
        exclusions.append(
            ExclusionRecord(
                dataset=dataset,
                cutoff_identity=cutoff_identity,
                reason=ExclusionReason.MISSING_CHRONOLOGY,
                excluded_count=len(missing_chronology_or_label),
            )
        )
        dropped = {record.sample_id for record in missing_chronology_or_label}
        retained = [record for record in retained if record.sample_id not in dropped]

    return PreparationOutcome(retained=tuple(retained), exclusions=tuple(exclusions))


def select_low_variance_features(
    training_population: tuple[PreparedSample, ...],
    scale_standardization_floor: PositiveFloat,
) -> frozenset[FeatureColumnIndex]:
    if not training_population:
        raise PreprocessingRuleError("low-variance selection requires a training population")
    dimension = len(training_population[0].features)
    if any(len(record.features) != dimension for record in training_population):
        raise PreprocessingRuleError("ragged feature vectors cannot be assessed")
    low_variance: set[FeatureColumnIndex] = set()
    for column in range(dimension):
        values = [record.features[column] for record in training_population]
        mean = sum(values) / len(values)
        variance = sum((value - mean) * (value - mean) for value in values) / len(values)
        if variance < scale_standardization_floor * scale_standardization_floor:
            low_variance.add(FeatureColumnIndex(column))
    return frozenset(low_variance)


@dataclass(frozen=True)
class SupportAssessment:
    malicious_support_before: SupportCount
    malicious_support_after: SupportCount
    control_support_before: SupportCount
    control_support_after: SupportCount

    def is_meeting_minimum(self, minimum_support_per_class: PositiveInt) -> SufficiencyFlag:
        return (
            self.malicious_support_before >= minimum_support_per_class
            and self.malicious_support_after >= minimum_support_per_class
            and self.control_support_before >= minimum_support_per_class
            and self.control_support_after >= minimum_support_per_class
        )


def is_adjacent_window_pooling_prohibited(
    support_a: SupportCount, support_b: SupportCount, minimum: PositiveInt
) -> ProhibitionFlag:
    return support_a >= minimum and support_b >= minimum


def is_horizon_confirmatory(availability: HorizonAvailability) -> ConfirmatoryFlag:
    return availability is HorizonAvailability.OBSERVABLE
