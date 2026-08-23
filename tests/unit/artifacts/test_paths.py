from __future__ import annotations

from pathlib import Path

from fedact.artifacts.paths import WorkspaceLayout
from fedact.config.loading import load_production_configuration
from fedact.domain.records import ExperimentName


def layout(repository_root: Path) -> WorkspaceLayout:
    loaded = load_production_configuration(repository_root / "configs" / "fedact.yaml")
    return WorkspaceLayout(
        repository_root=repository_root,
        artifacts=loaded.values.artifacts,
    )


def test_output_directories_render_from_the_authoritative_configuration_block(
    repository_root: Path,
) -> None:
    directories = layout(repository_root).output_directories()
    assert directories["preprocessing"] == repository_root / "outputs" / "preprocessing"
    assert directories["shared_models"] == repository_root / "outputs" / "artifacts" / "models"
    assert directories["staging"] == repository_root / "outputs" / "cache" / "staging"
    assert (
        directories["reproducibility"]
        == repository_root / "results" / "project_summary" / "reproducibility"
    )


def test_experiment_workspaces_use_configured_roots(repository_root: Path) -> None:
    workspace = layout(repository_root)
    name = ExperimentName("math-verification")
    assert (
        workspace.experiment_workspace(name) == repository_root / "outputs" / "experiments" / name
    )
    assert (
        workspace.result_experiment_directory(name)
        == repository_root / "results" / "experiments" / name
    )


def test_provenance_index_paths_come_from_configuration(repository_root: Path) -> None:
    workspace = layout(repository_root)
    assert (
        workspace.active_artifact_index()
        == repository_root
        / "outputs"
        / "artifacts"
        / "provenance"
        / "indexes"
        / "artifact_index.jsonl"
    )
    assert (
        workspace.dependency_index()
        == repository_root
        / "outputs"
        / "artifacts"
        / "provenance"
        / "indexes"
        / "dependency_index.json"
    )
    assert (
        workspace.evidence_index()
        == repository_root
        / "results"
        / "project_summary"
        / "reproducibility"
        / "execution"
        / "evidence_index.json"
    )
