from __future__ import annotations

import pytest

from fedact.domain.enums import ScientificAssumption, ScientificOutcome
from fedact.domain.records import SampleIdentifier, SplitCutoffIdentity
from fedact.operators.common import (
    ACTION_VALIDITY_CONSEQUENCE,
    OPERATOR_COVERAGE_CONSEQUENCE,
    EnumerationContractError,
    NormalizedParameterString,
    OperatorComposition,
    OperatorCoverageAudit,
    OperatorCoverageError,
    OperatorDomain,
    OperatorFamily,
    ValidityAuditEntry,
    enumerate_candidates,
    run_validity_audit,
)

CUTOFF = SplitCutoffIdentity("month-000024")
SAMPLE = SampleIdentifier("sample-1")


def family(name: str, order: int, grid: tuple[str, ...] = ("p1",)) -> OperatorFamily:
    return OperatorFamily(
        name=name,
        domain=OperatorDomain.WINDOWS_PE,
        listed_order=order,
        parameter_grid=tuple(NormalizedParameterString(parameter) for parameter in grid),
    )


def test_action_validity_contract_matches_the_roadmap_row() -> None:
    assert ACTION_VALIDITY_CONSEQUENCE.assumption is ScientificAssumption.ACTION_VALIDITY
    assert ACTION_VALIDITY_CONSEQUENCE.operationalization == "operator-specific validator"
    assert ACTION_VALIDITY_CONSEQUENCE.validation == "validity audit"
    assert ACTION_VALIDITY_CONSEQUENCE.failure_outcome is ScientificOutcome.ASSUMPTION_VIOLATION


def test_operator_coverage_contract_matches_the_roadmap_row() -> None:
    assert OPERATOR_COVERAGE_CONSEQUENCE.assumption is ScientificAssumption.OPERATOR_COVERAGE
    assert OPERATOR_COVERAGE_CONSEQUENCE.operationalization == "operator coverage audit"
    assert OPERATOR_COVERAGE_CONSEQUENCE.validation == "later-real coverage diagnostics"


def test_domain_validity_requires_all_four_validation_layers() -> None:
    entry = ValidityAuditEntry(
        operator_name="append-eof",
        domain=OperatorDomain.WINDOWS_PE,
        cutoff_identity=CUTOFF,
        structural_valid=True,
        execution_valid=True,
        maliciousness_preserved=True,
        behavior_preserved=True,
    )
    assert entry.is_domain_valid()
    broken = ValidityAuditEntry(
        operator_name="append-eof",
        domain=OperatorDomain.WINDOWS_PE,
        cutoff_identity=CUTOFF,
        structural_valid=True,
        execution_valid=False,
        maliciousness_preserved=True,
        behavior_preserved=True,
    )
    assert not broken.is_domain_valid()


def test_validity_audit_failure_makes_certified_transformations_unusable() -> None:
    entries = (
        ValidityAuditEntry(
            operator_name="zero-checksum",
            domain=OperatorDomain.WINDOWS_PE,
            cutoff_identity=CUTOFF,
            structural_valid=True,
            execution_valid=True,
            maliciousness_preserved=True,
            behavior_preserved=True,
        ),
        ValidityAuditEntry(
            operator_name="upx-pack",
            domain=OperatorDomain.WINDOWS_PE,
            cutoff_identity=CUTOFF,
            structural_valid=True,
            execution_valid=True,
            maliciousness_preserved=False,
            behavior_preserved=True,
        ),
    )
    with pytest.raises(OperatorCoverageError, match="unusable"):
        run_validity_audit(entries)


def test_coverage_denominator_zero_emits_abstention_requirement() -> None:
    audit = OperatorCoverageAudit(
        cutoff_identity=CUTOFF,
        operator_eligible_source_samples=0,
        samples_with_valid_nondegenerate_candidate=0,
        minimum_valid_coverage=0.50,
    )
    with pytest.raises(OperatorCoverageError, match="ABSTAIN_OPERATOR_COVERAGE_INSUFFICIENT"):
        audit.is_coverage_sufficient()


def test_coverage_below_minimum_is_operationally_empty() -> None:
    audit = OperatorCoverageAudit(
        cutoff_identity=CUTOFF,
        operator_eligible_source_samples=10,
        samples_with_valid_nondegenerate_candidate=4,
        minimum_valid_coverage=0.50,
    )
    assert audit.observed_coverage is not None
    assert not audit.is_coverage_sufficient()
    sufficient = OperatorCoverageAudit(
        cutoff_identity=CUTOFF,
        operator_eligible_source_samples=10,
        samples_with_valid_nondegenerate_candidate=6,
        minimum_valid_coverage=0.50,
    )
    assert sufficient.is_coverage_sufficient()


def test_composition_repeats_of_one_family_are_invalid() -> None:
    f1 = family("append", 0)
    params = (NormalizedParameterString("64"), NormalizedParameterString("64"))
    with pytest.raises(ValueError, match="may not repeat"):
        OperatorComposition(families=(f1, f1), parameters=params)


def test_composition_requires_aligned_families_and_parameters() -> None:
    f1 = family("append", 0)
    with pytest.raises(ValueError, match="align"):
        OperatorComposition(families=(f1,), parameters=())


def test_enumeration_covers_lengths_one_through_maximum() -> None:
    families = (family("append", 0, ("64", "256")), family("checksum", 1, ("zero",)))
    candidates = enumerate_candidates(families, 2, SAMPLE, CUTOFF)
    lengths = sorted({candidate.composition.families.__len__() for candidate in candidates})
    assert lengths == [1, 2]
    normalized_forms = {candidate.normalized_form for candidate in candidates}
    assert "append=64" in normalized_forms
    assert "append=64|checksum=zero" in normalized_forms


def test_enumeration_normalizes_permutations_to_one_candidate() -> None:
    first = family("append", 0, ("64",))
    second = family("rename", 1, ("data1",))
    direct = enumerate_candidates((first, second), 2, SAMPLE, CUTOFF)
    swapped = enumerate_candidates((second, first), 2, SAMPLE, CUTOFF)
    forms_direct = {candidate.normalized_form for candidate in direct}
    forms_swapped = {candidate.normalized_form for candidate in swapped}
    assert forms_direct == forms_swapped
    composed = [form for form in forms_direct if "|" in form]
    assert len(composed) == 1


def test_enumeration_is_deterministic_across_calls() -> None:
    families = (family("append", 0, ("64", "1024")), family("section", 1, ("ro-256",)))
    first = enumerate_candidates(families, 3, SAMPLE, CUTOFF)
    second = enumerate_candidates(families, 3, SAMPLE, CUTOFF)
    assert [candidate.normalized_form for candidate in first] == [
        candidate.normalized_form for candidate in second
    ]


def test_enumeration_rejects_invalid_maximum() -> None:
    fams = (family("append", 0),)
    with pytest.raises(EnumerationContractError):
        enumerate_candidates(fams, 0, SAMPLE, CUTOFF)


def test_enumeration_rejects_duplicate_listed_orders() -> None:
    fams = (family("a", 0), family("b", 0))
    with pytest.raises(EnumerationContractError, match="unique listed orders"):
        enumerate_candidates(fams, 1, SAMPLE, CUTOFF)
