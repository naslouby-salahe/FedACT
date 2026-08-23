from __future__ import annotations

import subprocess
from pathlib import Path


def test_deptry_reports_no_dependency_hygiene_problems(repository_root: Path) -> None:
    result = subprocess.run(
        ["uv", "run", "deptry", "."],
        capture_output=True,
        text=True,
        check=False,
        cwd=repository_root,
    )
    assert result.returncode == 0, f"deptry failed:\n{result.stdout}\n{result.stderr}"
