from __future__ import annotations

import shutil
from pathlib import Path

import pytest

_REAL_PRODUCTION_CONFIGURATION = Path(__file__).resolve().parents[3] / "configs" / "fedact.yaml"


@pytest.fixture
def repository_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "configs").mkdir(parents=True)
    (root / "pyproject.toml").write_text("", encoding="utf-8")
    shutil.copyfile(_REAL_PRODUCTION_CONFIGURATION, root / "configs" / "fedact.yaml")
    return root
