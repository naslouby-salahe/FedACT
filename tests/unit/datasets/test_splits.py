from __future__ import annotations

import pytest

from fedact.datasets.records import EligibilityStatus
from fedact.datasets.splits import (
    IndexInPopulation,
    SplitConstructionError,
    SplitPartition,
    construct_cutoff_split,
)
from fedact.domain.records import SampleIdentifier, SplitCutoffIdentity


def test_partition_counts_reflect_assignment_membership() -> None:
    split = construct_cutoff_split(
        cutoff_identity=SplitCutoffIdentity("c1"),
        sample_ids=tuple(SampleIdentifier(f"s{i}") for i in range(5)),
        training_indices=frozenset({IndexInPopulation(0), IndexInPopulation(1)}),
        validation_indices=frozenset({IndexInPopulation(2)}),
        test_indices=frozenset({IndexInPopulation(3), IndexInPopulation(4)}),
        operator_eligible=frozenset({SampleIdentifier("s0")}),
    )
    counts = split.partition_counts()
    assert counts.training == 2
    assert counts.validation == 1
    assert counts.test == 2
    assert counts.for_partition(SplitPartition.TRAINING) == 2
    assert counts.for_partition(SplitPartition.VALIDATION) == 1
    assert counts.for_partition(SplitPartition.TEST) == 2


def test_operator_eligible_ids_reflect_eligibility_status() -> None:
    split = construct_cutoff_split(
        cutoff_identity=SplitCutoffIdentity("c1"),
        sample_ids=tuple(SampleIdentifier(f"s{i}") for i in range(3)),
        training_indices=frozenset({IndexInPopulation(0)}),
        validation_indices=frozenset({IndexInPopulation(1)}),
        test_indices=frozenset({IndexInPopulation(2)}),
        operator_eligible=frozenset({SampleIdentifier("s0"), SampleIdentifier("s2")}),
    )
    assert split.operator_eligible_ids() == (SampleIdentifier("s0"), SampleIdentifier("s2"))
    ineligible = [
        assignment
        for assignment in split.assignments
        if assignment.eligibility_status is EligibilityStatus.OPERATOR_INELIGIBLE
    ]
    assert [assignment.sample_id for assignment in ineligible] == [SampleIdentifier("s1")]


def test_overlapping_partitions_are_rejected() -> None:
    with pytest.raises(SplitConstructionError):
        construct_cutoff_split(
            cutoff_identity=SplitCutoffIdentity("c1"),
            sample_ids=tuple(SampleIdentifier(f"s{i}") for i in range(2)),
            training_indices=frozenset({IndexInPopulation(0)}),
            validation_indices=frozenset({IndexInPopulation(0)}),
            test_indices=frozenset(),
            operator_eligible=frozenset(),
        )


def test_index_outside_population_is_rejected() -> None:
    with pytest.raises(SplitConstructionError):
        construct_cutoff_split(
            cutoff_identity=SplitCutoffIdentity("c1"),
            sample_ids=tuple(SampleIdentifier(f"s{i}") for i in range(2)),
            training_indices=frozenset({IndexInPopulation(5)}),
            validation_indices=frozenset(),
            test_indices=frozenset(),
            operator_eligible=frozenset(),
        )
