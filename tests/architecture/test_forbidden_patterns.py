from __future__ import annotations

import ast
import re
from pathlib import Path

FORBIDDEN_CALLS: frozenset[str] = frozenset({"print", "eval", "exec", "compile"})
TYPE_IGNORE_PATTERN = re.compile(r"#\s*type:\s*ignore")
SILENT_EXCEPT_PATTERN = re.compile(r"except[^:]*:\s*pass")


def forbidden_call_violations(repository_root: Path) -> list[str]:
    package_root = repository_root / "src"
    violations: list[str] = []
    for source_file in sorted(package_root.rglob("*.py")):
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            if node.func.id in FORBIDDEN_CALLS:
                violations.append(f"{source_file.name}:{node.lineno}: {node.func.id}()")
    return violations


def suppression_violations(repository_root: Path) -> list[str]:
    package_root = repository_root / "src"
    violations: list[str] = []
    for source_file in sorted(package_root.rglob("*.py")):
        text = source_file.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if TYPE_IGNORE_PATTERN.search(line):
                violations.append(f"{source_file.name}:{line_number}: type-ignore suppression")
            if SILENT_EXCEPT_PATTERN.search(line):
                violations.append(f"{source_file.name}:{line_number}: silently swallowed exception")
    return violations


def test_production_code_contains_no_forbidden_dynamic_calls(repository_root: Path) -> None:
    violations = forbidden_call_violations(repository_root)
    assert not violations, f"forbidden dynamic calls found: {violations}"


def test_production_code_contains_no_suppressions_or_silent_excepts(
    repository_root: Path,
) -> None:
    violations = suppression_violations(repository_root)
    assert not violations, f"suppressions/silent excepts found: {violations}"
