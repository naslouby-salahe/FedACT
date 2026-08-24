from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, NewType

from pydantic import Field

from fedact.config.models import PositiveInt
from fedact.datasets.records import EligibilityStatus
from fedact.domain.records import SampleIdentifier, SplitCutoffIdentity

IndexInPopulation = NewType("IndexInPopulation", int)


class SplitPartition(StrEnum):
    TRAINING = "training"
    VALIDATION = "validation"
    TEST = "test"


class SplitConstructionError(ValueError):
    pass


@dataclass(frozen=True)
class SplitAssignment:
    sample_id: SampleIdentifier
    cutoff_identity: SplitCutoffIdentity
    partition: SplitPartition
    eligibility_status: EligibilityStatus


@dataclass(frozen=True)
class CutoffSplit:
    cutoff_identity: SplitCutoffIdentity
    assignments: tuple[SplitAssignment, ...]

    def partition_counts(self) -> dict[SplitPartition, int]:
        counts: dict[SplitPartition, int] = dict.fromkeys(SplitPartition, 0)
        for assignment in self.assignments:
            counts[assignment.partition] += 1
        return counts

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


SupportCountValue = Annotated[int, Field(ge=0)]


def is_meeting_support_floor(
    counts: SupportCountValue, minimum_support_per_class: PositiveInt
) -> bool:
    return counts >= minimum_support_per_class
