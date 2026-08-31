from __future__ import annotations

from fedact.domain.enums import ExecutableWorkflowName, ScientificOutcome
from fedact.runtime.status import (
    ArtifactExecutionState,
    WorkflowExecutionState,
    WorkflowOutcomeRecord,
    outcome_for_workflow,
    workflows_with_recorded_outcomes,
)


def test_outcome_history_lookup_returns_the_recorded_outcome() -> None:
    history = (
        WorkflowOutcomeRecord(
            workflow=ExecutableWorkflowName.MATH_VERIFICATION,
            outcome=ScientificOutcome.PASS,
        ),
    )
    assert (
        outcome_for_workflow(history, ExecutableWorkflowName.MATH_VERIFICATION)
        is ScientificOutcome.PASS
    )


def test_outcome_history_lookup_returns_none_for_unknown_workflow() -> None:
    assert outcome_for_workflow((), ExecutableWorkflowName.SMOKE) is None


def test_recorded_workflows_are_exposed_as_a_set() -> None:
    history = (
        WorkflowOutcomeRecord(
            workflow=ExecutableWorkflowName.MATH_VERIFICATION,
            outcome=ScientificOutcome.PASS,
        ),
        WorkflowOutcomeRecord(
            workflow=ExecutableWorkflowName.SMOKE,
            outcome=ScientificOutcome.FAIL,
        ),
    )
    assert workflows_with_recorded_outcomes(history) == {
        ExecutableWorkflowName.MATH_VERIFICATION,
        ExecutableWorkflowName.SMOKE,
    }


def test_execution_state_enum_exposes_the_locked_values() -> None:
    assert {state.value for state in WorkflowExecutionState} == {
        "NOT_STARTED",
        "BLOCKED",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        "INVALID",
    }


def test_artifact_execution_state_enum_exposes_the_locked_values() -> None:
    assert {state.value for state in ArtifactExecutionState} == {
        "STAGING",
        "COMPLETE",
        "STALE",
        "INVALID",
    }
