from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fedact.config.models import ArtifactsConfig, RelativePosixPath
from fedact.domain.records import ExperimentName


@dataclass(frozen=True)
class WorkspaceLayout:
    repository_root: Path
    artifacts: ArtifactsConfig

    def resolve(self, relative_path: RelativePosixPath | ExperimentName) -> Path:
        return self.repository_root / str(relative_path)

    def output_directories(self) -> dict[str, Path]:
        directories = self.artifacts.directories
        return {
            "preprocessing": self.resolve(directories.preprocessing),
            "shared_artifacts": self.resolve(directories.shared_artifacts),
            "shared_models": self.resolve(directories.shared_models),
            "shared_scores": self.resolve(directories.shared_scores),
            "shared_fitted": self.resolve(directories.shared_fitted),
            "shared_baselines": self.resolve(directories.shared_baselines),
            "shared_derived": self.resolve(directories.shared_derived),
            "shared_provenance": self.resolve(directories.shared_provenance),
            "experiments": self.resolve(directories.experiments),
            "cache": self.resolve(directories.cache),
            "staging": self.resolve(directories.staging),
            "result_experiments": self.resolve(directories.result_experiments),
            "project_summary": self.resolve(directories.project_summary),
            "reproducibility": self.resolve(directories.reproducibility),
        }

    def experiment_workspace(self, experiment_name: ExperimentName) -> Path:
        return self.resolve(self.artifacts.directories.experiments) / experiment_name

    def result_experiment_directory(self, experiment_name: ExperimentName) -> Path:
        base = self.resolve(self.artifacts.directories.result_experiments) / experiment_name
        return base

    def active_artifact_index(self) -> Path:
        return self.resolve(self.artifacts.active_artifact_index)

    def dependency_index(self) -> Path:
        return self.resolve(self.artifacts.dependency_index)

    def evidence_index(self) -> Path:
        return self.resolve(self.artifacts.evidence_index)

    def staging_directory(self) -> Path:
        return self.resolve(self.artifacts.directories.staging)
