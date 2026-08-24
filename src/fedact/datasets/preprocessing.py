from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Annotated, NewType

from pydantic import Field

from fedact.config.models import PositiveFloat, PositiveInt
from fedact.datasets.chronology import HorizonAvailability
from fedact.datasets.records import ExclusionReason, ExclusionRecord
from fedact.domain.enums import DatasetSelector
from fedact.domain.records import SampleIdentifier, SplitCutoffIdentity
from fedact.domain.types import (
    BinaryLabel,
    FamilyName,
    MonthIndex,
    SampleCount,
)

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
        return SampleCount(
            sum(record.excluded_count for record in self.exclusions if record.reason is reason)
        )


def canonical_source_order_key(sample_id: SampleIdentifier) -> SampleIdentifier:
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
        winner = min(group, key=lambda item: canonical_source_order_key(item.sample_id))
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
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        if variance < scale_standardization_floor * scale_standardization_floor:
            low_variance.add(FeatureColumnIndex(column))
    return frozenset(low_variance)


@dataclass(frozen=True)
class SupportAssessment:
    malicious_support_before: SupportCount
    malicious_support_after: SupportCount
    control_support_before: SupportCount
    control_support_after: SupportCount

    def is_meeting_minimum(self, minimum_support_per_class: PositiveInt) -> bool:
        return (
            self.malicious_support_before >= minimum_support_per_class
            and self.malicious_support_after >= minimum_support_per_class
            and self.control_support_before >= minimum_support_per_class
            and self.control_support_after >= minimum_support_per_class
        )


def is_adjacent_window_pooling_prohibited(
    support_a: SupportCount, support_b: SupportCount, minimum: PositiveInt
) -> bool:
    return support_a >= minimum and support_b >= minimum


def is_horizon_confirmatory(availability: HorizonAvailability) -> bool:
    return availability is HorizonAvailability.OBSERVABLE
