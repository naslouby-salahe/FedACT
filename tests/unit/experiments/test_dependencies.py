from __future__ import annotations

import pytest

from fedact.domain.enums import ArtifactBoundary, WorkflowName
from fedact.experiments.dependencies import (
    ARTIFACT_BOUNDARY_CONTRACTS,
    WORKFLOW_ORDER,
    WORKFLOW_PREREQUISITES,
    DependencyFingerprint,
    UpstreamReferenceRequest,
    boundary_contract,
    resolve_shared_upstream_fingerprint,
    validate_workflow_prerequisite_graph,
)


def test_workflow_order_matches_the_locked_roadmap_sequence() -> None:
    assert WORKFLOW_ORDER == (
        WorkflowName.SCIENTIFIC_AND_CONFIGURATION_AUTHORITY,
        WorkflowName.MATHEMATICAL_AND_NUMERICAL_VERIFICATION,
        WorkflowName.SYNTHETIC_GENERATOR_SMOKE_VALIDATION,
        WorkflowName.SYNTHETIC_THEORY_AND_GEOMETRY_VALIDATION,
        WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT,
        WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION,
        WorkflowName.NESTED_PRE_CUTOFF_CALIBRATION,
        WorkflowName.REAL_DATA_ACTION_CERTIFICATE_VALIDATION,
        WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,
        WorkflowName.NOVELTY_CRITICAL_ABLATIONS,
        WorkflowName.FEDERATION_AND_COMPLEMENTARITY_EVALUATION,
        WorkflowName.ROBUSTNESS_AND_FAILURE_BOUNDARY_EVALUATION,
        WorkflowName.CROSS_CORPUS_GENERALIZATION,
        WorkflowName.COMMUNICATION_LIMITED_CLIENT_SELECTION,
        WorkflowName.STATISTICAL_SYNTHESIS,
        WorkflowName.MANUSCRIPT_EVIDENCE_GENERATION,
    )


def test_prerequisite_graph_is_acyclic_and_order_consistent() -> None:
    validate_workflow_prerequisite_graph()


def test_client_selection_does_not_block_statistical_synthesis() -> None:
    assert (
        WorkflowName.COMMUNICATION_LIMITED_CLIENT_SELECTION
        not in WORKFLOW_PREREQUISITES[WorkflowName.STATISTICAL_SYNTHESIS]
    )


def test_real_data_workflows_require_feasibility_parity_and_calibration() -> None:
    automatic = {
        WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT,
        WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION,
        WorkflowName.NESTED_PRE_CUTOFF_CALIBRATION,
    }
    downstream_real_data = {
        WorkflowName.REAL_DATA_ACTION_CERTIFICATE_VALIDATION,
        WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,
    }
    for workflow in downstream_real_data:
        assert automatic.issubset(set(WORKFLOW_PREREQUISITES[workflow]))


def test_every_boundary_except_inputs_and_reporting_has_a_boundary_consumer() -> None:
    for boundary, contract in ARTIFACT_BOUNDARY_CONTRACTS.items():
        if boundary in {ArtifactBoundary.INPUTS, ArtifactBoundary.REPORTING}:
            continue
        assert contract.consumers, f"boundary {boundary} has no consumers"


def test_inputs_are_consumed_by_all_later_boundaries() -> None:
    inputs = boundary_contract(ArtifactBoundary.INPUTS)
    assert set(inputs.consumers) == set(ArtifactBoundary) - {ArtifactBoundary.INPUTS}


def test_reporting_is_consumed_by_manuscript_only() -> None:
    reporting = boundary_contract(ArtifactBoundary.REPORTING)
    assert reporting.consumers == ()
    assert reporting.manuscript_only is True


def test_shared_upstream_requests_resolve_to_one_fingerprint_per_boundary() -> None:
    requests = (
        UpstreamReferenceRequest(
            consumer=WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,
            boundary=ArtifactBoundary.TRAINING_CHECKPOINTS,
            dependency_fingerprint=DependencyFingerprint("fp-1"),
        ),
        UpstreamReferenceRequest(
            consumer=WorkflowName.NOVELTY_CRITICAL_ABLATIONS,
            boundary=ArtifactBoundary.TRAINING_CHECKPOINTS,
            dependency_fingerprint=DependencyFingerprint("fp-1"),
        ),
    )
    resolved = resolve_shared_upstream_fingerprint(requests)
    assert resolved.for_boundary(ArtifactBoundary.TRAINING_CHECKPOINTS) == DependencyFingerprint(
        "fp-1"
    )


def test_conflicting_fingerprints_for_same_boundary_are_rejected() -> None:
    requests = (
        UpstreamReferenceRequest(
            consumer=WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,
            boundary=ArtifactBoundary.TRAINING_CHECKPOINTS,
            dependency_fingerprint=DependencyFingerprint("fp-1"),
        ),
        UpstreamReferenceRequest(
            consumer=WorkflowName.NOVELTY_CRITICAL_ABLATIONS,
            boundary=ArtifactBoundary.TRAINING_CHECKPOINTS,
            dependency_fingerprint=DependencyFingerprint("fp-2"),
        ),
    )
    with pytest.raises(ValueError):
        resolve_shared_upstream_fingerprint(requests)
