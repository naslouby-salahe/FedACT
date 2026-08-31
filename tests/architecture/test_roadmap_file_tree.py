from __future__ import annotations

from pathlib import Path

from tests.architecture.architecture_rules import (
    expected_production_python_paths,
    live_production_python_paths,
)

_MINIMAL_ROADMAP = """# 36. Repository Structure

```text
├── src/
│   └── fedact/
│       ├── __init__.py
│       └── app.py
├── tests/
    └── conftest.py
```
"""


def production_file_tree_violations(repository_root: Path) -> list[str]:
    expected = expected_production_python_paths(repository_root)
    live = live_production_python_paths(repository_root)
    violations = [
        f"extra production module vs roadmap §36: {path}" for path in sorted(live - expected)
    ]
    violations.extend(
        f"missing production module required by roadmap §36: {path}"
        for path in sorted(expected - live)
    )
    return violations


def test_live_production_tree_matches_roadmap_section_36(repository_root: Path) -> None:
    violations = production_file_tree_violations(repository_root)
    assert not violations, "roadmap file-tree violations:\n" + "\n".join(violations)


def test_file_tree_rule_detects_extra_and_missing_modules(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "Roadmap.md").write_text(_MINIMAL_ROADMAP, encoding="utf-8")
    package = tmp_path / "src" / "fedact"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "orphan.py").write_text("", encoding="utf-8")
    violations = production_file_tree_violations(tmp_path)
    assert any("orphan.py" in item for item in violations)
    assert any("app.py" in item for item in violations)


def test_file_tree_rule_accepts_exact_roadmap_tree(tmp_path: Path) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "Roadmap.md").write_text(_MINIMAL_ROADMAP, encoding="utf-8")
    package = tmp_path / "src" / "fedact"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "app.py").write_text("", encoding="utf-8")
    assert production_file_tree_violations(tmp_path) == []
