from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fedact.config.loading import LoadedConfiguration, load_production_configuration
from fedact.domain.enums import ExecutableWorkflowName, ScientificOutcome
from fedact.runtime.planning import ExecutionPlan, resolve_execution_plan

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

    def artifact_index_path(self) -> Path:
        return self.repository_root / self.configuration.values.artifacts.active_artifact_index

    def dependency_index_path(self) -> Path:
        return self.repository_root / self.configuration.values.artifacts.dependency_index

    def evidence_index_path(self) -> Path:
        return self.repository_root / self.configuration.values.artifacts.evidence_index

    def raw_data_root(self) -> Path:
        return self.repository_root / "data" / "raw"

    def is_raw_data_available(self) -> bool:
        raw_root = self.raw_data_root()
        return raw_root.is_dir() and any(raw_root.iterdir())

    def plan(
        self,
        completed: frozenset[ExecutableWorkflowName] = frozenset(),
        failed: frozenset[ExecutableWorkflowName] = frozenset(),
        outcomes: dict[ExecutableWorkflowName, ScientificOutcome] | None = None,
    ) -> ExecutionPlan:
        return resolve_execution_plan(completed=completed, failed=failed, outcomes=outcomes)


def discover_repository_root(start: Path) -> Path:
    candidate = start.resolve()
    for current in (candidate, *candidate.parents):
        if (current / "pyproject.toml").is_file() and (
            current / "configs" / "fedact.yaml"
        ).is_file():
            return current
    raise FileNotFoundError(f"FedACT repository root not found above {start}")
