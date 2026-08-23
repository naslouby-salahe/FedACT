from __future__ import annotations

import ast
import re
from pathlib import Path

SNAKE_CASE_PATTERN = re.compile(r"^_{0,2}[a-z][a-z0-9_]*$")
PASCAL_CASE_PATTERN = re.compile(r"^_{0,1}[A-Z][A-Za-z0-9]*$")
ALLOWED_SHORT_NAMES: frozenset[str] = frozenset(
    {"fit", "run", "map", "key", "top", "sum", "min", "max", "np", "pd"}
)


def identifier_violations(repository_root: Path) -> list[str]:
    package_root = repository_root / "src"
    violations: list[str] = []
    for source_file in sorted(package_root.rglob("*.py")):
        module_ok = SNAKE_CASE_PATTERN.match(source_file.stem) or source_file.stem == "__init__"
        if not module_ok:
            violations.append(f"{source_file.name}: module name violates snake_case policy")
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if not PASCAL_CASE_PATTERN.match(node.name):
                    violations.append(f"{source_file.name}:{node.lineno}: class {node.name}")
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                if name.startswith("__") and name.endswith("__"):
                    continue
                if not SNAKE_CASE_PATTERN.match(name) or (
                    len(name.replace("_", "")) < 4 and name not in ALLOWED_SHORT_NAMES
                ):
                    violations.append(f"{source_file.name}:{node.lineno}: function {name}")
    return violations


def vague_name_violations(repository_root: Path) -> list[str]:
    package_root = repository_root / "src"
    vague_names = {"data2", "temp", "tmp", "foo", "bar", "baz", "stuff", "misc", "handle", "do_it"}
    violations: list[str] = []
    for source_file in sorted(package_root.rglob("*.py")):
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id.lower() in vague_names:
                violations.append(f"{source_file.name}:{node.lineno}: vague identifier {node.id}")
    return violations


def test_module_class_and_function_names_follow_descriptive_conventions(
    repository_root: Path,
) -> None:
    violations = identifier_violations(repository_root)
    assert not violations, f"naming policy violations found: {violations}"


def test_vague_or_misleading_identifiers_are_rejected(repository_root: Path) -> None:
    violations = vague_name_violations(repository_root)
    assert not violations, f"vague identifiers found: {violations}"
