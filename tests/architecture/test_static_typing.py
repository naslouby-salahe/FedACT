from __future__ import annotations

import subprocess
from pathlib import Path


def test_repository_strict_pyright_passes(repository_root: Path) -> None:
    result = subprocess.run(
        ["uv", "run", "pyright"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"pyright strict failed:\n{result.stdout}\n{result.stderr}"
