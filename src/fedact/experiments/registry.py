from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

from fedact.config.loading import LoadedConfiguration
from fedact.domain.types import ExecutableWorkflowName, OptionalFlag, RoadmapSectionId


class ExperimentRuntime(Protocol):
    @property
    def repository_root(self) -> Path:
        return cast(Path, None)

    @property
    def configuration(self) -> LoadedConfiguration:
        return cast(LoadedConfiguration, None)


def experiment_directory(application: ExperimentRuntime, workflow: ExecutableWorkflowName) -> Path:
    return (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / workflow
    )


@dataclass(frozen=True)
class RegisteredWorkflow:
    name: ExecutableWorkflowName
    section: RoadmapSectionId
    dependencies: tuple[ExecutableWorkflowName, ...]
    optional: OptionalFlag


WORKFLOW_REGISTRY: tuple[RegisteredWorkflow, ...] = (
    RegisteredWorkflow(ExecutableWorkflowName.PREPROCESS, "§10", (), False),
    RegisteredWorkflow(ExecutableWorkflowName.SMOKE, "§21", (), False),
    RegisteredWorkflow(
        ExecutableWorkflowName.MATH_VERIFICATION,
        "§13",
        (),
        False,
    ),
    RegisteredWorkflow(
        ExecutableWorkflowName.SYNTHETIC_GEOMETRY,
        "§21",
        (ExecutableWorkflowName.MATH_VERIFICATION, ExecutableWorkflowName.SMOKE),
        False,
    ),
    RegisteredWorkflow(
        ExecutableWorkflowName.BASELINE_PARITY,
        "§14",
        (ExecutableWorkflowName.PREPROCESS,),
        False,
    ),
    RegisteredWorkflow(
        ExecutableWorkflowName.NESTED_CALIBRATION,
        "§25",
        (ExecutableWorkflowName.PREPROCESS, ExecutableWorkflowName.BASELINE_PARITY),
        False,
    ),
    RegisteredWorkflow(
        ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION,
        "§26",
        (
            ExecutableWorkflowName.PREPROCESS,
            ExecutableWorkflowName.BASELINE_PARITY,
            ExecutableWorkflowName.NESTED_CALIBRATION,
        ),
        False,
    ),
    RegisteredWorkflow(
        ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
        "§27",
        (ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION,),
        False,
    ),
    RegisteredWorkflow(
        ExecutableWorkflowName.ABLATIONS,
        "§28",
        (ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
        False,
    ),
    RegisteredWorkflow(
        ExecutableWorkflowName.FEDERATION,
        "§29",
        (ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
        False,
    ),
    RegisteredWorkflow(
        ExecutableWorkflowName.FAILURE_BOUNDARIES,
        "§30",
        (ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
        False,
    ),
    RegisteredWorkflow(
        ExecutableWorkflowName.CROSS_CORPUS,
        "§31",
        (
            ExecutableWorkflowName.PREPROCESS,
            ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
            ExecutableWorkflowName.FAILURE_BOUNDARIES,
        ),
        False,
    ),
    RegisteredWorkflow(
        ExecutableWorkflowName.CLIENT_SELECTION,
        "§32",
        (ExecutableWorkflowName.FEDERATION,),
        True,
    ),
    RegisteredWorkflow(
        ExecutableWorkflowName.STATISTICAL_SYNTHESIS,
        "§33",
        (
            ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION,
            ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
            ExecutableWorkflowName.ABLATIONS,
            ExecutableWorkflowName.FEDERATION,
            ExecutableWorkflowName.FAILURE_BOUNDARIES,
            ExecutableWorkflowName.CROSS_CORPUS,
        ),
        False,
    ),
)

REGISTRY_NAMES = {workflow.name: workflow for workflow in WORKFLOW_REGISTRY}
CLI_SELECTABLE_WORKFLOWS = tuple(workflow.name for workflow in WORKFLOW_REGISTRY)


def registered_workflow(name: ExecutableWorkflowName) -> RegisteredWorkflow:
    try:
        return REGISTRY_NAMES[name]
    except KeyError as error:
        raise ValueError(f"unregistered workflow: {name}") from error
