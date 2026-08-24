from __future__ import annotations

import subprocess
from pathlib import Path


def run_tool(repository_root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
        cwd=repository_root,
    )


def assert_tool_passes(repository_root: Path, command: list[str], label: str) -> None:
    result = run_tool(repository_root, command)
    assert result.returncode == 0, f"{label} failed:\n{result.stdout}\n{result.stderr}"


def test_ruff_formatting_passes(repository_root: Path) -> None:
    assert_tool_passes(
        repository_root,
        ["uv", "run", "ruff", "format", "--check", "src", "tests"],
        "ruff format",
    )


def test_ruff_linting_passes(repository_root: Path) -> None:
    assert_tool_passes(
        repository_root,
        ["uv", "run", "ruff", "check", "src", "tests"],
        "ruff check",
    )


def test_strict_pyright_passes(repository_root: Path) -> None:
    assert_tool_passes(repository_root, ["uv", "run", "pyright"], "pyright strict")


def test_dependency_hygiene_passes(repository_root: Path) -> None:
    assert_tool_passes(repository_root, ["uv", "run", "deptry", "."], "deptry")


def test_high_confidence_dead_code_is_absent(repository_root: Path) -> None:
    assert_tool_passes(
        repository_root,
        ["uv", "run", "vulture", "src", "tests", "--min-confidence", "80"],
        "vulture",
    )
