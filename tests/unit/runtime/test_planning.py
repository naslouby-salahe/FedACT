from __future__ import annotations

from fedact.domain.enums import ExecutableWorkflowName as W
from fedact.domain.enums import ScientificOutcome
from fedact.runtime.planning import resolve_execution_plan
from fedact.runtime.status import WorkflowExecutionState, WorkflowOutcomeRecord


def _passed(*workflows: W) -> tuple[WorkflowOutcomeRecord, ...]:
    return tuple(
        WorkflowOutcomeRecord(workflow=workflow, outcome=ScientificOutcome.PASS)
        for workflow in workflows
    )


def test_fresh_plan_offers_preprocess_smoke_and_math_verification() -> None:
    plan = resolve_execution_plan()
    assert set(plan.executable) == {
        W.PREPROCESS,
        W.SMOKE,
        W.MATH_VERIFICATION,
    }


def test_downstream_workflows_stay_blocked_until_prerequisites_complete() -> None:
    plan = resolve_execution_plan(_passed(W.MATH_VERIFICATION))
    entry = plan.entry(W.SYNTHETIC_GEOMETRY)
    assert entry.status is WorkflowExecutionState.BLOCKED
    assert entry.blocking_dependencies == (W.SMOKE,)


def test_completing_internal_chain_unlocks_certificate_validation() -> None:
    plan = resolve_execution_plan(_passed(W.PREPROCESS, W.BASELINE_PARITY, W.NESTED_CALIBRATION))
    assert W.ACTION_CERTIFICATE_VALIDATION in plan.executable


def test_completed_workflows_report_completed_status() -> None:
    plan = resolve_execution_plan(_passed(W.PREPROCESS))
    assert plan.entry(W.PREPROCESS).status is WorkflowExecutionState.COMPLETED


def test_failed_workflow_reports_failed_without_blocking_siblings() -> None:
    outcomes = _passed(W.PREPROCESS, W.SMOKE, W.MATH_VERIFICATION) + (
        WorkflowOutcomeRecord(workflow=W.SYNTHETIC_GEOMETRY, outcome=ScientificOutcome.FAIL),
    )
    plan = resolve_execution_plan(outcomes)
    assert plan.entry(W.SYNTHETIC_GEOMETRY).status is WorkflowExecutionState.FAILED
    assert plan.entry(W.BASELINE_PARITY).status is WorkflowExecutionState.NOT_STARTED


def test_recorded_outcomes_surface_in_plan_entries() -> None:
    outcomes = (
        WorkflowOutcomeRecord(workflow=W.PREPROCESS, outcome=ScientificOutcome.PASS),
        WorkflowOutcomeRecord(
            workflow=W.MATH_VERIFICATION, outcome=ScientificOutcome.ABSTENTION_EXPECTED
        ),
    )
    plan = resolve_execution_plan(outcomes)
    assert plan.entry(W.PREPROCESS).recorded_outcome is ScientificOutcome.PASS
    assert plan.entry(W.MATH_VERIFICATION).recorded_outcome is ScientificOutcome.ABSTENTION_EXPECTED


def test_client_selection_is_marked_optional_and_never_blocks_synthesis() -> None:
    plan = resolve_execution_plan(
        _passed(
            W.PREPROCESS,
            W.SMOKE,
            W.MATH_VERIFICATION,
            W.SYNTHETIC_GEOMETRY,
            W.BASELINE_PARITY,
            W.NESTED_CALIBRATION,
            W.ACTION_CERTIFICATE_VALIDATION,
            W.PROSPECTIVE_EVALUATION,
            W.ABLATIONS,
            W.FEDERATION,
            W.FAILURE_BOUNDARIES,
            W.CROSS_CORPUS,
        )
    )
    client_entry = plan.entry(W.CLIENT_SELECTION)
    assert client_entry.optional is True
    synthesis = plan.entry(W.STATISTICAL_SYNTHESIS)
    assert W.CLIENT_SELECTION not in synthesis.blocking_dependencies
    assert W.STATISTICAL_SYNTHESIS in plan.executable
