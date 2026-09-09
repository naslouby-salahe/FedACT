from __future__ import annotations

from typer.testing import CliRunner

from fedact.cli import app


def test_preprocess_accepts_a_dataset_selector() -> None:
    result = CliRunner().invoke(app, ["preprocess", "lamda", "--repository-root", "."])
    assert result.exit_code == 0
    assert "preprocess scope: lamda" in result.output
