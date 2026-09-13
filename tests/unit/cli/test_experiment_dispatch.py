from __future__ import annotations

from pathlib import Path

import pytest

from fedact.domain.types import ExecutableWorkflowName
from fedact.workflow import run_experiment


@pytest.fixture
def repository_root(tmp_path: Path, repository_root: Path) -> Path:
    return repository_root


def test_run_experiment_dispatches_baseline_parity_after_materializing_dependencies(
    repository_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_experiment(ExecutableWorkflowName.BASELINE_PARITY, True, repository_root)
    output = capsys.readouterr().out
    assert f"workflow: {ExecutableWorkflowName.BASELINE_PARITY}" in output
    assert "roadmap section:" in output
    assert "overwrite: scoped to this workflow's artifacts" in output
    assert "baseline parity validation completed" in output
