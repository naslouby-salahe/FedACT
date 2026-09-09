from __future__ import annotations

from pathlib import Path

import pytest

REQUIRED_COMPONENTS = frozenset({"__init__.py", "cli.py", "workflow.py", "artifacts.py", "domain", "config", "data", "learning", "certification", "experiments", "analysis"})
FORBIDDEN_COMPONENTS = frozenset({"app.py", "baselines", "calibration", "cli", "core", "datasets", "evaluation", "models", "operators", "reporting", "runtime", "scoring", "storage", "training"})
REQUIRED_TEST_AREAS = frozenset({"architecture", "integration", "scientific", "unit"})

def architecture_shape_violations(repository_root: Path) -> list[str]:
    package_root = repository_root / "src" / "fedact"
    if not package_root.is_dir():
        return ["src/fedact package root is missing"]
    present = {path.name for path in package_root.iterdir() if path.name != "__pycache__"}
    violations = [f"missing production component: {name}" for name in sorted(REQUIRED_COMPONENTS - present)]
    violations.extend(f"unknown production component remains: {name}" for name in sorted(present - REQUIRED_COMPONENTS))
    violations.extend(f"obsolete production component remains: {name}" for name in sorted(present & FORBIDDEN_COMPONENTS))
    for package in REQUIRED_COMPONENTS - {"__init__.py", "cli.py", "workflow.py", "artifacts.py"}:
        if not (package_root / package / "__init__.py").is_file():
            violations.append(f"package lacks __init__.py: {package}")
    tests_root = repository_root / "tests"
    violations.extend(f"missing test area: tests/{area}" for area in sorted(REQUIRED_TEST_AREAS) if not (tests_root / area).is_dir())
    for obsolete in ("quality", "smoke", "e2e"):
        if (tests_root / obsolete).exists():
            violations.append(f"obsolete test area remains: tests/{obsolete}")
    return violations

def test_repository_shape_matches_the_consolidated_architecture(repository_root: Path) -> None:
    assert architecture_shape_violations(repository_root) == []

def test_repository_shape_accepts_consolidated_architecture(repository_root: Path) -> None:
    assert architecture_shape_violations(repository_root) == []

@pytest.mark.parametrize("relative_path", ["src/fedact/utils.py", "src/fedact/core/__init__.py", "src/fedact/cli/main.py", "tests/quality/test_old.py"])
def test_repository_shape_rejects_structural_escape_hatches(tmp_path: Path, relative_path: str) -> None:
    package_root = tmp_path / "src" / "fedact"
    package_root.mkdir(parents=True)
    for component in REQUIRED_COMPONENTS:
        target = package_root / component
        if "." in component:
            target.write_text("", encoding="utf-8")
        else:
            target.mkdir()
            (target / "__init__.py").write_text("", encoding="utf-8")
    for area in REQUIRED_TEST_AREAS:
        (tmp_path / "tests" / area).mkdir(parents=True)
    target = tmp_path / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("", encoding="utf-8")
    assert architecture_shape_violations(tmp_path)
