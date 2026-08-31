from __future__ import annotations

from dataclasses import dataclass

from fedact.domain.enums import ExecutableWorkflowName, ScientificOutcome
from fedact.domain.records import OptionalFlag
from fedact.runtime.status import (
    WorkflowExecutionState,
    WorkflowOutcomeHistory,
    outcome_for_workflow,
    workflows_with_recorded_outcomes,
)

WORKFLOW_DEPENDENCIES: dict[ExecutableWorkflowName, tuple[ExecutableWorkflowName, ...]] = {
    ExecutableWorkflowName.PREPROCESS: (),
    ExecutableWorkflowName.SMOKE: (),
    ExecutableWorkflowName.MATH_VERIFICATION: (),
    ExecutableWorkflowName.SYNTHETIC_GEOMETRY: (
        ExecutableWorkflowName.MATH_VERIFICATION,
        ExecutableWorkflowName.SMOKE,
    ),
    ExecutableWorkflowName.BASELINE_PARITY: (ExecutableWorkflowName.PREPROCESS,),
    ExecutableWorkflowName.NESTED_CALIBRATION: (
        ExecutableWorkflowName.PREPROCESS,
        ExecutableWorkflowName.BASELINE_PARITY,
    ),
    ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION: (
        ExecutableWorkflowName.PREPROCESS,
        ExecutableWorkflowName.BASELINE_PARITY,
        ExecutableWorkflowName.NESTED_CALIBRATION,
    ),
    ExecutableWorkflowName.PROSPECTIVE_EVALUATION: (
        ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION,
    ),
    ExecutableWorkflowName.ABLATIONS: (ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
    ExecutableWorkflowName.FEDERATION: (ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
    ExecutableWorkflowName.FAILURE_BOUNDARIES: (ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
    ExecutableWorkflowName.CROSS_CORPUS: (
        ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
        ExecutableWorkflowName.FAILURE_BOUNDARIES,
        ExecutableWorkflowName.PREPROCESS,
    ),
    ExecutableWorkflowName.CLIENT_SELECTION: (ExecutableWorkflowName.FEDERATION,),
    ExecutableWorkflowName.STATISTICAL_SYNTHESIS: (
        ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION,
        ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
        ExecutableWorkflowName.ABLATIONS,
        ExecutableWorkflowName.FEDERATION,
        ExecutableWorkflowName.FAILURE_BOUNDARIES,
        ExecutableWorkflowName.CROSS_CORPUS,
    ),
}

OPTIONAL_WORKFLOWS: frozenset[ExecutableWorkflowName] = frozenset(
    {ExecutableWorkflowName.CLIENT_SELECTION}
)


@dataclass(frozen=True)
class WorkflowPlanEntry:
    workflow: ExecutableWorkflowName
    status: WorkflowExecutionState
    blocking_reasons: tuple[str, ...]
    optional: OptionalFlag
    blocking_dependencies: tuple[ExecutableWorkflowName, ...] = ()
    recorded_outcome: ScientificOutcome | None = None

    @property
    def name(self) -> ExecutableWorkflowName:
        return self.workflow


@dataclass(frozen=True)
class ExecutionPlan:
    entries: tuple[WorkflowPlanEntry, ...]

    @property
    def blocked(self) -> tuple[WorkflowPlanEntry, ...]:
        return tuple(
            entry for entry in self.entries if entry.status is WorkflowExecutionState.BLOCKED
        )

    @property
    def executable(self) -> frozenset[ExecutableWorkflowName]:
        return frozenset(
            entry.workflow
            for entry in self.entries
            if entry.status is WorkflowExecutionState.NOT_STARTED
        )

    def executable_workflows(self) -> tuple[ExecutableWorkflowName, ...]:
        return tuple(
            entry.workflow
            for entry in self.entries
            if entry.status is WorkflowExecutionState.NOT_STARTED
        )

    def blocked_workflows(self) -> tuple[ExecutableWorkflowName, ...]:
        return tuple(
            entry.workflow
            for entry in self.entries
            if entry.status is WorkflowExecutionState.BLOCKED
        )

    def entry(self, workflow: ExecutableWorkflowName) -> WorkflowPlanEntry:
        for item in self.entries:
            if item.workflow is workflow:
                return item
        raise KeyError(f"Workflow {workflow.value} not found in plan")


def _evaluate_dependency_blockers(
    dependencies: tuple[ExecutableWorkflowName, ...],
    outcomes: WorkflowOutcomeHistory,
) -> tuple[tuple[str, ...], tuple[ExecutableWorkflowName, ...]]:
    recorded = workflows_with_recorded_outcomes(outcomes)
    blocking: list[str] = []
    blocking_deps: list[ExecutableWorkflowName] = []
    for dependency in dependencies:
        if dependency not in recorded:
            blocking.append(f"dependency_unmet: {dependency.value}")
            blocking_deps.append(dependency)
        elif outcome_for_workflow(outcomes, dependency) is ScientificOutcome.FAIL:
            blocking.append(f"dependency_outcome_failed: {dependency.value}")
            blocking_deps.append(dependency)
    return tuple(blocking), tuple(blocking_deps)


def _build_entry_for_workflow(
    workflow: ExecutableWorkflowName,
    dependencies: tuple[ExecutableWorkflowName, ...],
    outcomes: WorkflowOutcomeHistory,
) -> WorkflowPlanEntry:
    is_optional = workflow in OPTIONAL_WORKFLOWS
    outcome = outcome_for_workflow(outcomes, workflow)

    if outcome is not None:
        status = (
            WorkflowExecutionState.COMPLETED
            if outcome != ScientificOutcome.FAIL
            else WorkflowExecutionState.FAILED
        )
        return WorkflowPlanEntry(
            workflow=workflow,
            status=status,
            blocking_reasons=(outcome.value,),
            optional=is_optional,
            blocking_dependencies=(),
            recorded_outcome=outcome,
        )

    blocking, blocking_deps = _evaluate_dependency_blockers(dependencies, outcomes)
    plan_status = (
        WorkflowExecutionState.NOT_STARTED if not blocking else WorkflowExecutionState.BLOCKED
    )
    return WorkflowPlanEntry(
        workflow=workflow,
        status=plan_status,
        blocking_reasons=blocking,
        optional=is_optional,
        blocking_dependencies=blocking_deps,
        recorded_outcome=outcome,
    )


def resolve_execution_plan(outcomes: WorkflowOutcomeHistory = ()) -> ExecutionPlan:
    entries = [
        _build_entry_for_workflow(workflow, dependencies, outcomes)
        for workflow, dependencies in WORKFLOW_DEPENDENCIES.items()
    ]
    return ExecutionPlan(entries=tuple(entries))
