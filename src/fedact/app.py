from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fedact.artifacts.manifests import read_workflow_result
from fedact.artifacts.paths import WorkspaceLayout
from fedact.config.loading import LoadedConfiguration, load_production_configuration
from fedact.domain.enums import ExecutableWorkflowName
from fedact.domain.records import DataAvailabilityFlag, ExperimentName
from fedact.runtime.planning import ExecutionPlan, resolve_execution_plan
from fedact.runtime.state import WorkflowOutcomeHistory, WorkflowOutcomeRecord

SYSEXITS_EX_UNAVAILABLE = 69
PRODUCER_NOT_REGISTERED_EXIT_CODE = SYSEXITS_EX_UNAVAILABLE


@dataclass(frozen=True)
class Application:
    repository_root: Path
    configuration: LoadedConfiguration

    @classmethod
    def from_repository_root(cls, repository_root: Path) -> Application:
        configuration = load_production_configuration(repository_root / "configs" / "fedact.yaml")
        return cls(repository_root=repository_root.resolve(), configuration=configuration)

    def workspace_layout(self) -> WorkspaceLayout:
        return WorkspaceLayout(
            repository_root=self.repository_root,
            artifacts=self.configuration.values.artifacts,
        )

    def artifact_index_path(self) -> Path:
        return self.workspace_layout().active_artifact_index()

    def dependency_index_path(self) -> Path:
        return self.workspace_layout().dependency_index()

    def evidence_index_path(self) -> Path:
        return self.workspace_layout().evidence_index()

    def result_experiment_directory(self, workflow: ExecutableWorkflowName) -> Path:
        return self.workspace_layout().result_experiment_directory(ExperimentName(workflow.value))

    def raw_data_root(self) -> Path:
        return self.repository_root / "data" / "raw"

    def is_raw_data_available(self) -> DataAvailabilityFlag:
        raw_root = self.raw_data_root()
        return raw_root.is_dir() and any(raw_root.iterdir())

    def recorded_outcomes(self) -> WorkflowOutcomeHistory:
        return tuple(
            WorkflowOutcomeRecord(workflow=workflow, outcome=record.scientific_outcome)
            for workflow in ExecutableWorkflowName
            if (record := read_workflow_result(self.result_experiment_directory(workflow)))
            is not None
        )

    def plan(self) -> ExecutionPlan:
        return resolve_execution_plan(self.recorded_outcomes())


def discover_repository_root(start: Path) -> Path:
    candidate = start.resolve()
    for current in (candidate, *candidate.parents):
        if (current / "pyproject.toml").is_file() and (
            current / "configs" / "fedact.yaml"
        ).is_file():
            return current
    raise FileNotFoundError(f"FedACT repository root not found above {start}")
