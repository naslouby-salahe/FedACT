from __future__ import annotations

from dataclasses import dataclass

from fedact.domain.enums import ExecutableWorkflowName, ScientificOutcome
from fedact.experiments.registry import REGISTRY_NAMES, WORKFLOW_REGISTRY

INTERNAL_STAGE_DEPENDENCIES: dict[ExecutableWorkflowName, tuple[ExecutableWorkflowName, ...]] = {
    ExecutableWorkflowName.PREPROCESS: (),
    ExecutableWorkflowName.SMOKE: (),
    ExecutableWorkflowName.BASELINE_PARITY: (ExecutableWorkflowName.PREPROCESS,),
    ExecutableWorkflowName.NESTED_CALIBRATION: (
        ExecutableWorkflowName.PREPROCESS,
        ExecutableWorkflowName.BASELINE_PARITY,
    ),
}


def _workflow_dependencies() -> dict[ExecutableWorkflowName, tuple[ExecutableWorkflowName, ...]]:
    dependencies = dict(INTERNAL_STAGE_DEPENDENCIES)
    for workflow in WORKFLOW_REGISTRY:
        dependencies[workflow.name] = workflow.required_dependencies
    return dependencies


@dataclass(frozen=True)
class WorkflowPlanEntry:
    name: ExecutableWorkflowName
    status: str
    blocking_dependencies: tuple[ExecutableWorkflowName, ...]
    optional: bool
    recorded_outcome: ScientificOutcome | None = None


@dataclass(frozen=True)
class ExecutionPlan:
    entries: tuple[WorkflowPlanEntry, ...]

    def entry(self, name: ExecutableWorkflowName) -> WorkflowPlanEntry:
        for candidate in self.entries:
            if candidate.name is name:
                return candidate
        raise KeyError(f"workflow is not part of the execution plan: {name}")

    @property
    def executable(self) -> tuple[ExecutableWorkflowName, ...]:
        return tuple(entry.name for entry in self.entries if entry.status == "executable")

    @property
    def blocked(self) -> tuple[ExecutableWorkflowName, ...]:
        return tuple(entry.name for entry in self.entries if entry.status == "blocked")


def resolve_execution_plan(
    completed: frozenset[ExecutableWorkflowName] = frozenset(),
    failed: frozenset[ExecutableWorkflowName] = frozenset(),
    outcomes: dict[ExecutableWorkflowName, ScientificOutcome] | None = None,
) -> ExecutionPlan:
    dependencies = _workflow_dependencies()
    statuses: dict[ExecutableWorkflowName, tuple[str, tuple[ExecutableWorkflowName, ...]]] = {}

    changed = True
    while changed:
        changed = False
        for name, required in dependencies.items():
            current_status = statuses.get(name, ("blocked", tuple(required)))[0]
            if current_status != "blocked":
                continue
            unmet = tuple(dep for dep in required if dep not in completed)
            if not unmet or name in completed:
                statuses[name] = (
                    "completed" if name in completed else "executable",
                    (),
                )
                changed = True
            else:
                statuses[name] = ("blocked", unmet)

    entries: list[WorkflowPlanEntry] = []
    for name in dependencies:
        status, blocking = statuses[name]
        if name in failed and status != "completed":
            status = "failed"
        entries.append(
            WorkflowPlanEntry(
                name=name,
                status=status,
                blocking_dependencies=blocking,
                optional=name in REGISTRY_NAMES and REGISTRY_NAMES[name].optional,
                recorded_outcome=(outcomes or {}).get(name),
            )
        )
    return ExecutionPlan(entries=tuple(entries))
