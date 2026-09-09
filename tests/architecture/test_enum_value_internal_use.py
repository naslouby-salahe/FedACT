from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.architecture.architecture_rules import (
    enum_definitions,
    module_name,
    parse_source,
    production_source_files,
    relative_source_path,
    terminal_name,
)

BOUNDARY_MODULES = frozenset(
    {
        "fedact.cli",
        "fedact.data.ember2024",
        "fedact.analysis.reporting",
        "fedact.config.loading",
        "fedact.artifacts",
        "fedact.artifacts",
        "fedact.artifacts",
    }
)


def is_boundary_module(module: str) -> bool:
    return any(module == prefix or module.startswith(prefix + ".") for prefix in BOUNDARY_MODULES)


def _enum_typed_names(tree: ast.Module) -> set[str]:
    local_enum_names = set(enum_definitions(tree))
    typed: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            annotation_names = {n.id for n in ast.walk(node.annotation) if isinstance(n, ast.Name)}
            if annotation_names & local_enum_names:
                typed.add(node.target.id)
        elif isinstance(node, ast.Assign):
            value = node.value
            root = value.value if isinstance(value, ast.Attribute) else value
            if isinstance(root, ast.Name) and root.id in local_enum_names:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        typed.add(target.id)
        elif isinstance(node, ast.arg) and node.annotation is not None:
            annotation_names = {n.id for n in ast.walk(node.annotation) if isinstance(n, ast.Name)}
            if annotation_names & local_enum_names:
                typed.add(node.arg)
    return local_enum_names | typed


def internal_enum_value_violations_for_tree(module: str, path: str, tree: ast.Module) -> list[str]:
    enum_typed_names = _enum_typed_names(tree)
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or node.attr != "value":
            continue
        base = node.value
        if isinstance(base, ast.Name) and base.id in enum_typed_names:
            violations.append(f"{path}:{node.lineno}: internal enum .value unwrap of {base.id}")
        elif isinstance(base, ast.Attribute):
            root = terminal_name(base)
            if root in enum_typed_names:
                violations.append(f"{path}:{node.lineno}: internal enum .value unwrap of {root}")
    return violations


def internal_enum_value_violations(repository_root: Path) -> list[str]:
    violations: list[str] = []
    for source_file in production_source_files(repository_root):
        module = module_name(repository_root, source_file)
        if is_boundary_module(module):
            continue
        path = relative_source_path(repository_root, source_file)
        violations.extend(
            internal_enum_value_violations_for_tree(module, path, parse_source(source_file))
        )
    return violations


def snippet_violations(snippet: str) -> list[str]:
    return internal_enum_value_violations_for_tree(
        "fedact.certification.example", "example.py", ast.parse(snippet)
    )


def test_internal_domain_code_does_not_unwrap_enum_values(repository_root: Path) -> None:
    violations = internal_enum_value_violations(repository_root)
    assert not violations, "internal enum .value unwrapping:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    "snippet",
    [
        (
            "from enum import StrEnum\n"
            "class Status(StrEnum):\n"
            "    PASS = 'pass'\n"
            "def render(s: Status) -> None:\n"
            "    print(s.value)\n"
        ),
        (
            "from enum import StrEnum\n"
            "class Status(StrEnum):\n"
            "    PASS = 'pass'\n"
            "status = Status.PASS\n"
            "if status.value == 'pass':\n"
            "    pass\n"
        ),
    ],
)
def test_internal_enum_value_rule_rejects_known_unwrap(snippet: str) -> None:
    assert snippet_violations(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        (
            "from enum import StrEnum\n"
            "class Status(StrEnum):\n"
            "    PASS = 'pass'\n"
            "def compare(a: Status, b: Status) -> bool:\n"
            "    return a is b\n"
        ),
        (
            "from enum import StrEnum\n"
            "class Status(StrEnum):\n"
            "    PASS = 'pass'\n"
            "def render(s: Status) -> Status:\n"
            "    return s\n"
        ),
    ],
)
def test_internal_enum_value_rule_accepts_domain_comparisons(snippet: str) -> None:
    assert snippet_violations(snippet) == []
