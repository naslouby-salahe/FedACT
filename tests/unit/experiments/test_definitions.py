from __future__ import annotations

from fedact.domain.enums import ArtifactBoundary, WorkflowName
from fedact.experiments.definitions import (
    OPTIONAL_WORKFLOW_NAMES,
    WORKFLOW_CONTRACTS,
    workflow_contract,
)


def test_every_workflow_has_a_contract() -> None:
    assert set(WORKFLOW_CONTRACTS) == set(WorkflowName)


def test_every_contract_records_all_required_items() -> None:
    for contract in WORKFLOW_CONTRACTS.values():
        assert contract.scientific_purpose
        assert contract.required_upstream_artifacts
        assert all(
            isinstance(boundary, ArtifactBoundary)
            for boundary in contract.required_upstream_artifacts
        )
        assert contract.manipulations_and_comparators
        assert contract.metrics
        assert contract.applicable_statistical_analysis
        assert contract.resulting_artifacts


def test_only_client_selection_is_optional() -> None:
    assert (
        frozenset({WorkflowName.COMMUNICATION_LIMITED_CLIENT_SELECTION}) == OPTIONAL_WORKFLOW_NAMES
    )


def test_statistical_synthesis_consumes_only_evaluation_boundary() -> None:
    synthesis = workflow_contract(WorkflowName.STATISTICAL_SYNTHESIS)
    assert synthesis.required_upstream_artifacts == (ArtifactBoundary.EVALUATION,)


def test_manuscript_generation_consumes_only_analysis_boundary() -> None:
    manuscript = workflow_contract(WorkflowName.MANUSCRIPT_EVIDENCE_GENERATION)
    assert manuscript.required_upstream_artifacts == (ArtifactBoundary.ANALYSIS,)
