from __future__ import annotations

import ast
import re
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

ENUM_ROLE_TOKENS = frozenset(
    {
        "action",
        "artifact",
        "attack",
        "boundary",
        "dataset",
        "decision",
        "format",
        "geometry",
        "lifecycle",
        "method",
        "outcome",
        "phase",
        "polarity",
        "reason",
        "scheme",
        "selector",
        "split",
        "state",
        "status",
        "verdict",
        "workflow",
    }
)


def identifier_tokens(name: str) -> set[str]:
    snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
    return {token for token in re.split(r"[^a-z0-9]+", snake) if token}


def enum_classes(tree: ast.Module) -> dict[str, list[str]]:
    definitions: dict[str, list[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(terminal_name(base) in {"Enum", "StrEnum", "IntEnum"} for base in node.bases):
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


def nearest_class(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> ast.ClassDef | None:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, ast.ClassDef):
            return current
    return None


def owner_enum_names(owners: set[tuple[str, str]]) -> set[str]:
    return {enum_name for _, enum_name in owners}


def name_is_enum_shaped(name: str, owners: set[tuple[str, str]]) -> bool:
    tokens = identifier_tokens(name)
    if tokens & ENUM_ROLE_TOKENS:
        return True
    owner_tokens = {
        token for enum_name in owner_enum_names(owners) for token in identifier_tokens(enum_name)
    }
    return bool(tokens & owner_tokens)


def target_names(node: ast.AST) -> list[str]:
    names: list[str] = []
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            names.append(child.id)
        elif isinstance(child, ast.Attribute):
            names.append(child.attr)
    return names


def annotation_mentions_owner(annotation: ast.expr | None, owners: set[tuple[str, str]]) -> bool:
    if annotation is None:
        return False
    owner_names = owner_enum_names(owners)
    return any(
        terminal_name(node) in owner_names
        for node in ast.walk(annotation)
        if isinstance(node, (ast.Name, ast.Attribute))
    )


def enclosing_function(
    node: ast.AST, parents: dict[ast.AST, ast.AST]
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current
    return None


def default_parameter_for_literal(
    node: ast.AST,
    parents: dict[ast.AST, ast.AST],
) -> ast.arg | None:
    function = enclosing_function(node, parents)
    if function is None:
        return None
    positional = [*function.args.posonlyargs, *function.args.args]
    defaults = function.args.defaults
    offset = len(positional) - len(defaults)
    for index, default in enumerate(defaults):
        if node is default or node in set(ast.walk(default)):
            return positional[offset + index]
    for argument, default in zip(function.args.kwonlyargs, function.args.kw_defaults, strict=True):
        if default is not None and (node is default or node in set(ast.walk(default))):
            return argument
    return None


def enum_semantic_use_site(
    node: ast.Constant,
    parents: dict[ast.AST, ast.AST],
    owners: set[tuple[str, str]],
) -> bool:
    default_parameter = default_parameter_for_literal(node, parents)
    if default_parameter is not None:
        return name_is_enum_shaped(default_parameter.arg, owners) or annotation_mentions_owner(
            default_parameter.annotation, owners
        )

    current: ast.AST = node
    while current in parents:
        parent = parents[current]
        if isinstance(parent, ast.AnnAssign):
            return any(
                name_is_enum_shaped(name, owners) for name in target_names(parent.target)
            ) or annotation_mentions_owner(parent.annotation, owners)
        if isinstance(parent, ast.Assign):
            return any(
                name_is_enum_shaped(name, owners)
                for target in parent.targets
                for name in target_names(target)
            )
        if isinstance(parent, ast.keyword) and parent.arg:
            return name_is_enum_shaped(parent.arg, owners)
        if isinstance(parent, ast.Compare):
            names = [
                name for child in [parent.left, *parent.comparators] for name in target_names(child)
            ]
            return any(name_is_enum_shaped(name, owners) for name in names)
        if isinstance(parent, ast.MatchValue):
            match_node: ast.AST = parent
            while match_node in parents and not isinstance(parents[match_node], ast.Match):
                match_node = parents[match_node]
            if match_node in parents and isinstance(parents[match_node], ast.Match):
                subject = parents[match_node].subject
                return any(name_is_enum_shaped(name, owners) for name in target_names(subject))
            return False
        if isinstance(parent, ast.Return):
            function = enclosing_function(parent, parents)
            return function is not None and (
                annotation_mentions_owner(function.returns, owners)
                or name_is_enum_shaped(function.name, owners)
            )
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            break
        current = parent
    return False


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
        if not enum_semantic_use_site(node, parents, owners):
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


def test_enums_are_unique_consumed_and_not_bypassed_by_raw_values(repository_root: Path) -> None:
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
        "def choose(status: object) -> None:\n"
        "    match status:\n"
        "        case 'PASS':\n"
        "            return\n",
        "def execute(status: str = 'PASS') -> None:\n    pass\n",
        "from fedact.domain.enums import ScientificOutcome\n"
        "def outcome() -> ScientificOutcome:\n"
        "    return 'PASS'\n",
    ],
)
def test_raw_enum_value_rule_rejects_use_site_bypasses(snippet: str) -> None:
    catalog = {"PASS": {("fedact.domain.enums", "ScientificOutcome")}}
    assert raw_enum_literal_violations_for_tree(
        "fedact.example", ast.parse(snippet), "example.py", catalog
    )


@pytest.mark.parametrize(
    "snippet",
    [
        "folder = 'analysis'\n",
        "message = 'PASS'\n",
        "from pathlib import Path\npath = Path('analysis')\n",
    ],
)
def test_raw_enum_value_rule_ignores_non_semantic_string_uses(snippet: str) -> None:
    catalog = {
        "PASS": {("fedact.domain.enums", "ScientificOutcome")},
        "analysis": {("fedact.domain.enums", "ArtifactBoundary")},
    }
    assert (
        raw_enum_literal_violations_for_tree(
            "fedact.example", ast.parse(snippet), "example.py", catalog
        )
        == []
    )


def test_enum_member_usage_is_accepted() -> None:
    snippet = "from fedact.domain.enums import ScientificOutcome\nstatus = ScientificOutcome.PASS\n"
    catalog = {"PASS": {("fedact.domain.enums", "ScientificOutcome")}}
    assert (
        raw_enum_literal_violations_for_tree(
            "fedact.example", ast.parse(snippet), "example.py", catalog
        )
        == []
    )


def test_enum_definition_literals_are_not_reported_as_bypasses() -> None:
    snippet = "from enum import StrEnum\nclass ScientificOutcome(StrEnum):\n    PASS = 'PASS'\n"
    catalog = {"PASS": {("fedact.example", "ScientificOutcome")}}
    assert (
        raw_enum_literal_violations_for_tree(
            "fedact.example", ast.parse(snippet), "example.py", catalog
        )
        == []
    )
