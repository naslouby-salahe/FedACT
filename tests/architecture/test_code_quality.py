from __future__ import annotations

import subprocess
from pathlib import Path


def run_tool(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )


def test_ruff_formatting_and_linting_pass(repository_root: Path) -> None:
    format_result = run_tool(["uv", "run", "ruff", "format", "--check", "src", "tests"])
    assert format_result.returncode == 0, (
        f"ruff format failed:\n{format_result.stdout}\n{format_result.stderr}"
    )
    lint_result = run_tool(["uv", "run", "ruff", "check", "src", "tests"])
    assert lint_result.returncode == 0, (
        f"ruff check failed:\n{lint_result.stdout}\n{lint_result.stderr}"
    )
