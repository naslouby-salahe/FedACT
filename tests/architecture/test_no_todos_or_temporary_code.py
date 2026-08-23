from __future__ import annotations

import re
from pathlib import Path

TEMPORARY_MARKER_PATTERN = re.compile(
    r"\b(TODO|FIXME|HACK|XXX|WIP|TEMPORARY|PLACEHOLDER)\b", re.IGNORECASE
)
COMMENTED_CODE_PATTERN = re.compile(r"^\s*#\s*(def |class |return |import |from )")


def temporary_residue_violations(repository_root: Path) -> list[str]:
    roots = [repository_root / "src", repository_root / "tests"]
    violations: list[str] = []
    for root in roots:
        for source_file in sorted(root.rglob("*.py")):
            if source_file.name == "test_no_todos_or_temporary_code.py":
                continue
            for line_number, line in enumerate(
                source_file.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if TEMPORARY_MARKER_PATTERN.search(line):
                    violations.append(f"{source_file.name}:{line_number}: {line.strip()}")
                if COMMENTED_CODE_PATTERN.match(line):
                    violations.append(
                        f"{source_file.name}:{line_number}: commented-out implementation residue"
                    )
    return violations


def test_sources_contain_no_todo_markers_or_commented_out_implementations(
    repository_root: Path,
) -> None:
    violations = temporary_residue_violations(repository_root)
    assert not violations, f"temporary development residue found: {violations[:10]}"


def test_marker_fixture_is_detected(tmp_path: Path) -> None:
    package_dir = tmp_path / "src"
    package_dir.mkdir()
    violating = package_dir / "violating.py"
    violating.write_text("value = compute()  # FIXME later\n", encoding="utf-8")
    assert any("FIXME" in line for line in temporary_residue_violations(tmp_path))
