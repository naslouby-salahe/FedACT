from __future__ import annotations

import pytest

from fedact.domain.types import ExecutableWorkflowName, ScientificOutcome
from fedact.workflow import (
    Application,
    WorkflowExecutionState,
    run_experiment,
)

FOUNDATIONAL_WORKFLOWS = (
    ExecutableWorkflowName.BASELINE_PARITY,
    ExecutableWorkflowName.MATH_VERIFICATION,
)


@pytest.mark.parametrize("workflow", FOUNDATIONAL_WORKFLOWS)
def test_run_experiment_completes_dependency_free_workflows(
    workflow: ExecutableWorkflowName,
    lamda_corpus_application: Application,
    capsys: pytest.CaptureFixture[str],
) -> None:
    run_experiment(workflow, True, lamda_corpus_application.repository_root)
    output = capsys.readouterr().out
    assert f"workflow: {workflow}" in output
    assert "roadmap section:" in output
    assert "overwrite: scoped to this workflow's artifacts" in output
    entry = lamda_corpus_application.plan().entry(workflow)
    assert entry.status is WorkflowExecutionState.COMPLETED
    assert entry.recorded_outcome is ScientificOutcome.PASS


def test_run_experiment_records_an_insufficient_evidence_outcome(
    lamda_corpus_application: Application,
) -> None:
    run_experiment(
        ExecutableWorkflowName.NESTED_CALIBRATION,
        True,
        lamda_corpus_application.repository_root,
    )
    entry = lamda_corpus_application.plan().entry(ExecutableWorkflowName.NESTED_CALIBRATION)
    assert entry.status is WorkflowExecutionState.INVALID
    assert entry.recorded_outcome is ScientificOutcome.INSUFFICIENT_EVIDENCE


def test_a_dependency_that_does_not_pass_blocks_its_dependents(
    lamda_corpus_application: Application,
) -> None:
    with pytest.raises(RuntimeError, match="did not complete"):
        run_experiment(
            ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
            True,
            lamda_corpus_application.repository_root,
        )
    entry = lamda_corpus_application.plan().entry(ExecutableWorkflowName.PROSPECTIVE_EVALUATION)
    assert entry.status is WorkflowExecutionState.BLOCKED
    assert entry.status is not WorkflowExecutionState.COMPLETED
