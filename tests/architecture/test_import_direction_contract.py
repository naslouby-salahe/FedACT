from __future__ import annotations

import subprocess
from pathlib import Path


def test_import_linter_layered_architecture_contract_holds(repository_root: Path) -> None:
    result = subprocess.run(
        ["uv", "run", "lint-imports"],
        capture_output=True,
        text=True,
        check=False,
        cwd=repository_root,
    )
    assert result.returncode == 0, (
        f"import-linter contracts broken:\n{result.stdout}\n{result.stderr}"
    )
