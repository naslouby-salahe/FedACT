from __future__ import annotations

from fedact.domain.enums import WorkflowName
from fedact.experiments import (
    WORKFLOW_ORDER,
    WORKFLOW_PREREQUISITES,
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
