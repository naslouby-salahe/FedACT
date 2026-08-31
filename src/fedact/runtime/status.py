from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fedact.domain.enums import ExecutableWorkflowName, ScientificOutcome


class WorkflowExecutionState(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    BLOCKED = "BLOCKED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INVALID = "INVALID"


@dataclass(frozen=True)
class WorkflowOutcomeRecord:
    workflow: ExecutableWorkflowName
    outcome: ScientificOutcome


type WorkflowOutcomeHistory = tuple[WorkflowOutcomeRecord, ...]


def outcome_for_workflow(
    history: WorkflowOutcomeHistory, workflow: ExecutableWorkflowName
) -> ScientificOutcome | None:
    for record in history:
        if record.workflow is workflow:
            return record.outcome
    return None


def workflows_with_recorded_outcomes(
    history: WorkflowOutcomeHistory,
) -> frozenset[ExecutableWorkflowName]:
    return frozenset(record.workflow for record in history)


class ArtifactExecutionState(StrEnum):
    STAGING = "STAGING"
    COMPLETE = "COMPLETE"
    STALE = "STALE"
    INVALID = "INVALID"
