from __future__ import annotations

from fedact.domain.enums import WorkflowName
from fedact.experiments import (
    OPTIONAL_WORKFLOW_NAMES,
    WORKFLOW_CONTRACTS,
    workflow_contract,
)


def test_every_workflow_has_a_contract() -> None:
    assert set(WORKFLOW_CONTRACTS) == set(WorkflowName)


def test_every_contract_records_all_required_items() -> None:
    for contract in WORKFLOW_CONTRACTS.values():
        assert contract.scientific_purpose
        assert contract.manipulations_and_comparators
        assert contract.metrics
        assert contract.applicable_statistical_analysis
        assert contract.resulting_artifacts


def test_only_client_selection_is_optional() -> None:
    assert (
        frozenset({WorkflowName.COMMUNICATION_LIMITED_CLIENT_SELECTION}) == OPTIONAL_WORKFLOW_NAMES
    )


def test_math_verification_consumes_only_inputs() -> None:
    verification = workflow_contract(WorkflowName.MATHEMATICAL_AND_NUMERICAL_VERIFICATION)
    assert verification.scientific_purpose
    assert verification.metrics
