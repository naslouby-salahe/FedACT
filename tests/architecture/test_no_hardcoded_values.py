from __future__ import annotations

import ast
from pathlib import Path


def find_governed_constant_violations(path: Path, governed: frozenset[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            value = node.value
            targets = node.targets
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            value = node.value
            targets = [node.target]
        else:
            continue
        for target in targets:
            if not isinstance(target, ast.Name) or not target.id.isupper():
                continue
            if isinstance(value, ast.Constant) and isinstance(value.value, (int, float)):
                literal = repr(value.value)
                if literal in governed:
                    violations.append(f"{path.name}:{node.lineno}: {target.id} = {literal}")
    return violations


def scan_source_tree(repository_root: Path, governed: frozenset[str]) -> list[str]:
    package_root = repository_root / "src" / "fedact"
    return [
        violation
        for source_file in sorted(package_root.rglob("*.py"))
        for violation in find_governed_constant_violations(source_file, governed)
    ]


def test_source_tree_contains_no_hardcoded_governed_values(
    repository_root: Path, governed_scalar_literals: frozenset[str]
) -> None:
    assert governed_scalar_literals, "governed literal discovery must be non-empty"
    violations = scan_source_tree(repository_root, governed_scalar_literals)
    assert not violations, (
        f"hardcoded governed values found outside configuration authority: {violations}"
    )


def test_governed_literal_fixture_is_detected(
    tmp_path: Path, governed_scalar_literals: frozenset[str]
) -> None:
    assert "500" in governed_scalar_literals
    violating_file = tmp_path / "violating.py"
    violating_file.write_text("BOOTSTRAP_RESAMPLES = 500\n", encoding="utf-8")
    violations = find_governed_constant_violations(violating_file, governed_scalar_literals)
    assert violations == ["violating.py:1: BOOTSTRAP_RESAMPLES = 500"]


def test_ungoverned_literal_fixture_passes(
    tmp_path: Path, governed_scalar_literals: frozenset[str]
) -> None:
    clean_file = tmp_path / "clean.py"
    clean_file.write_text("LOCAL_UNGOVERNED_SCALE = 4242\n\nnormal_value = 500\n", encoding="utf-8")
    assert find_governed_constant_violations(clean_file, governed_scalar_literals) == []


def test_non_uppercase_assignment_is_not_treated_as_a_governed_constant(
    tmp_path: Path, governed_scalar_literals: frozenset[str]
) -> None:
    local_file = tmp_path / "local_usage.py"
    local_file.write_text("resamples_used_here = 500\n", encoding="utf-8")
    assert find_governed_constant_violations(local_file, governed_scalar_literals) == []
