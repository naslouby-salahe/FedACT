from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

import pytest

from tests.architecture.architecture_rules import (
    module_name,
    parse_source,
    production_source_files,
    relative_source_path,
    terminal_name,
)


def enum_classes(tree: ast.Module) -> dict[str, list[str]]:
    definitions: dict[str, list[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(
            terminal_name(base) in {"Enum", "StrEnum", "IntEnum"} for base in node.bases
        ):
            continue
        values: list[str] = []
        for item in node.body:
            if not isinstance(item, ast.Assign) or len(item.targets) != 1:
                continue
            if not isinstance(item.targets[0], ast.Name):
                continue
            if isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                values.append(item.value.value)
        definitions[node.name] = values
    return definitions


def enum_catalog(
    repository_root: Path,
) -> tuple[dict[str, set[tuple[str, str]]], dict[tuple[str, str], list[str]]]:
    values: dict[str, set[tuple[str, str]]] = defaultdict(set)
    definitions: dict[tuple[str, str], list[str]] = {}
    for source_file in production_source_files(repository_root):
        module = module_name(repository_root, source_file)
        for enum_name, enum_values in enum_classes(parse_source(source_file)).items():
            definitions[(module, enum_name)] = enum_values
            for value in enum_values:
                values[value].add((module, enum_name))
    return dict(values), definitions


def duplicate_enum_value_violations(
    definitions: dict[tuple[str, str], list[str]],
) -> list[str]:
    violations: list[str] = []
    for (module, enum_name), values in definitions.items():
        seen: set[str] = set()
        duplicates: set[str] = set()
        for value in values:
            if value in seen:
                duplicates.add(value)
            seen.add(value)
        if duplicates:
            violations.append(
                f"{module}.{enum_name} contains duplicate values {sorted(duplicates)}"
            )
    return violations


def nearest_class(
    node: ast.AST, parents: dict[ast.AST, ast.AST]
) -> ast.ClassDef | None:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, ast.ClassDef):
            return current
    return None


def raw_enum_literal_violations_for_tree(
    module: str,
    tree: ast.Module,
    path: str,
    catalog: dict[str, set[tuple[str, str]]],
) -> list[str]:
    own_enums = enum_classes(tree)
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
            continue
        owners = catalog.get(node.value)
        if not owners:
            continue
        containing_class = nearest_class(node, parents)
        if containing_class is not None and containing_class.name in own_enums:
            continue
        enum_names = sorted(f"{owner_module}.{enum_name}" for owner_module, enum_name in owners)
        violations.append(
            f"{path}:{node.lineno}: raw enum value {node.value!r} bypasses {enum_names}"
        )
    return violations


def external_enum_reference_violations(
    repository_root: Path,
    definitions: dict[tuple[str, str], list[str]],
) -> list[str]:
    references: dict[str, set[str]] = defaultdict(set)
    for source_file in production_source_files(repository_root):
        module = module_name(repository_root, source_file)
        tree = parse_source(source_file)
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                references[node.id].add(module)
            elif isinstance(node, ast.Attribute):
                references[node.attr].add(module)
    violations: list[str] = []
    for defining_module, enum_name in definitions:
        consumers = references.get(enum_name, set()) - {defining_module}
        if not consumers:
            violations.append(
                f"{defining_module}.{enum_name} is never consumed outside its defining module"
            )
    return violations


def enum_integrity_violations(repository_root: Path) -> list[str]:
    catalog, definitions = enum_catalog(repository_root)
    violations = duplicate_enum_value_violations(definitions)
    for source_file in production_source_files(repository_root):
        violations.extend(
            raw_enum_literal_violations_for_tree(
                module_name(repository_root, source_file),
                parse_source(source_file),
                relative_source_path(repository_root, source_file),
                catalog,
            )
        )
    violations.extend(external_enum_reference_violations(repository_root, definitions))
    return violations


def test_enums_are_unique_consumed_and_not_bypassed_by_raw_values(
    repository_root: Path,
) -> None:
    violations = enum_integrity_violations(repository_root)
    assert not violations, "enum integrity violations:\n" + "\n".join(violations)


def test_duplicate_enum_values_are_rejected() -> None:
    definitions = {("fedact.example", "Status"): ["PASS", "PASS"]}
    assert duplicate_enum_value_violations(definitions)


@pytest.mark.parametrize(
    "snippet",
    [
        "status = 'PASS'\n",
        "def accepted(status: object) -> bool:\n    return status == 'PASS'\n",
        "def choose(status: object) -> None:\n    match status:\n        case 'PASS':\n            return\n",
        "def execute(status: str = 'PASS') -> None:\n    pass\n",
    ],
)
def test_raw_enum_value_rule_rejects_use_site_bypasses(snippet: str) -> None:
    catalog = {"PASS": {("fedact.domain.enums", "ScientificOutcome")}}
    assert raw_enum_literal_violations_for_tree(
        "fedact.example", ast.parse(snippet), "example.py", catalog
    )


def test_enum_member_usage_is_accepted() -> None:
    snippet = (
        "from fedact.domain.enums import ScientificOutcome\n"
        "status = ScientificOutcome.PASS\n"
    )
    catalog = {"PASS": {("fedact.domain.enums", "ScientificOutcome")}}
    assert raw_enum_literal_violations_for_tree(
        "fedact.example", ast.parse(snippet), "example.py", catalog
    ) == []


def test_enum_definition_literals_are_not_reported_as_bypasses() -> None:
    snippet = (
        "from enum import StrEnum\n"
        "class ScientificOutcome(StrEnum):\n"
        "    PASS = 'PASS'\n"
    )
    catalog = {"PASS": {("fedact.example", "ScientificOutcome")}}
    assert raw_enum_literal_violations_for_tree(
        "fedact.example", ast.parse(snippet), "example.py", catalog
    ) == []
