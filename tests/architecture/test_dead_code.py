from __future__ import annotations

import subprocess
from pathlib import Path


def test_vulture_reports_no_high_confidence_dead_code(repository_root: Path) -> None:
    result = subprocess.run(
        ["uv", "run", "vulture", "src", "tests", "--min-confidence", "80"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"vulture found dead code:\n{result.stdout}\n{result.stderr}"
