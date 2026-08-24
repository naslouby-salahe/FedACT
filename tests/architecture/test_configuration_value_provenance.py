from __future__ import annotations

import ast
import re
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest
import yaml

from tests.architecture.architecture_rules import (
    SAFE_NUMERIC_LITERALS,
    module_name,
    parse_source,
    production_source_files,
    relative_source_path,
)

CONFIGURATION_AUTHORITY_MODULES = frozenset(
    {
        "fedact.config.models",
        "fedact.config.validation",
        "fedact.config.loading",
    }
)
TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9]*")


def config_value_index(payload: str) -> dict[str, frozenset[str]]:
    loaded = cast(object, yaml.safe_load(payload))
    paths_by_value: dict[str, set[str]] = {}

    def walk(value: object, path: tuple[str, ...]) -> None:
        if isinstance(value, bool):
            return
        if isinstance(value, (int, float)):
            if value in SAFE_NUMERIC_LITERALS:
                return
            paths_by_value.setdefault(repr(value), set()).add(".".join(path))
            return
        if isinstance(value, dict):
            mapping = cast(dict[object, object], value)
            for key, child in mapping.items():
                walk(child, (*path, str(key)))
            return
        if isinstance(value, list):
            for child in cast(list[object], value):
                walk(child, path)

    walk(loaded, ())
    return {value: frozenset(paths) for value, paths in paths_by_value.items()}


def name_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw in TOKEN_PATTERN.findall(text):
        expanded = re.sub(r"(?<!^)(?=[A-Z])", "_", raw).lower().split("_")
        tokens.update(token for token in expanded if len(token) > 2)
    return tokens


def path_tokens(paths: frozenset[str]) -> set[str]:
    return {token for path in paths for token in name_tokens(path)}


def numeric_value(node: ast.AST) -> int | float | None:
    if isinstance(node, ast.Constant) and not isinstance(node.value, bool):
        if isinstance(node.value, (int, float)):
            return node.value
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and not isinstance(node.operand.value, bool)
        and isinstance(node.operand.value, (int, float))
    ):
        return -node.operand.value
    return None


def numeric_nodes(tree: ast.Module) -> Iterator[ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    for node in ast.walk(tree):
        value = numeric_value(node)
        if value is None:
            continue
        if isinstance(node, ast.Constant):
            parent = parents.get(node)
            if isinstance(parent, ast.UnaryOp) and isinstance(parent.op, ast.USub):
                continue
        yield node


def context_tokens(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> set[str]:
    current = node
    context: ast.AST = node
    while current in parents:
        current = parents[current]
        context = current
        if isinstance(
            current,
            (
                ast.Assign,
                ast.AnnAssign,
                ast.Return,
                ast.Call,
                ast.Compare,
                ast.If,
                ast.While,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            break
    names: list[str] = []
    for child in ast.walk(context):
        if isinstance(child, ast.Name):
            names.append(child.id)
        elif isinstance(child, ast.Attribute):
            names.append(child.attr)
        elif isinstance(child, ast.keyword) and child.arg:
            names.append(child.arg)
    return name_tokens(" ".join(names))


def node_within(node: ast.AST, root: ast.AST) -> bool:
    return any(candidate is node for candidate in ast.walk(root))


def is_function_default(node: ast.AST, parents: dict[ast.AST, ast.AST]) -> bool:
    current = node
    while current in parents:
        parent = parents[current]
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defaults = [
                *parent.args.defaults,
                *(default for default in parent.args.kw_defaults if default is not None),
            ]
            return any(node_within(node, default) for default in defaults)
        current = parent
    return False


def hardcoded_configuration_violations_for_tree(
    module: str,
    tree: ast.Module,
    path: str,
    values: dict[str, frozenset[str]],
) -> list[str]:
    if module in CONFIGURATION_AUTHORITY_MODULES:
        return []
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    violations: list[str] = []
    for node in numeric_nodes(tree):
        value = numeric_value(node)
        if value is None or value in SAFE_NUMERIC_LITERALS:
            continue
        rendered = repr(value)
        governed_paths = values.get(rendered, frozenset())
        if is_function_default(node, parents):
            violations.append(
                f"{path}:{getattr(node, 'lineno', 0)}: numeric default {rendered} must come "
                "from typed configuration"
            )
            continue
        if not governed_paths:
            continue
        overlap = context_tokens(node, parents) & path_tokens(governed_paths)
        parent = parents.get(node)
        arithmetic_magic = isinstance(parent, ast.BinOp)
        if overlap or arithmetic_magic:
            violations.append(
                f"{path}:{getattr(node, 'lineno', 0)}: governed literal {rendered} "
                f"matches {sorted(governed_paths)} via {sorted(overlap)}"
            )
    return violations


def hardcoded_configuration_violations(
    repository_root: Path, payload: str
) -> list[str]:
    values = config_value_index(payload)
    violations: list[str] = []
    for source_file in production_source_files(repository_root):
        violations.extend(
            hardcoded_configuration_violations_for_tree(
                module_name(repository_root, source_file),
                parse_source(source_file),
                relative_source_path(repository_root, source_file),
                values,
            )
        )
    return violations


def violations_for_snippet(snippet: str, payload: str) -> list[str]:
    return hardcoded_configuration_violations_for_tree(
        "fedact.example", ast.parse(snippet), "example.py", config_value_index(payload)
    )


def test_governed_values_are_read_from_typed_configuration(
    repository_root: Path, production_payload: str
) -> None:
    violations = hardcoded_configuration_violations(repository_root, production_payload)
    assert not violations, "hardcoded configuration values:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    "snippet",
    [
        "BOOTSTRAP_RESAMPLES = 500\n",
        "resamples_used_here = 500\n",
        "def execute(resamples: int = 500) -> None:\n    pass\n",
        "def execute(schedule: tuple[int, int] = (200, 500)) -> None:\n    pass\n",
        "def execute(config: object = factory(500)) -> None:\n    pass\n",
        "def execute() -> None:\n    bootstrap(resamples=500)\n",
        "def execute(resamples: int) -> bool:\n    return resamples >= 500\n",
        "def execute() -> None:\n    bootstrap(500)\n",
        "sensitivity_alpha = [0.01, 0.05, 0.10, 0.20]\n",
        "def execute(base: float) -> float:\n    return base * 0.95\n",
    ],
)
def test_configuration_rule_rejects_known_literal_escape_hatches(
    snippet: str, production_payload: str
) -> None:
    assert violations_for_snippet(snippet, production_payload), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "def execute(value: int = 1) -> int:\n    return value\n",
        "def execute(index: int) -> int:\n    return index + 1\n",
        "def execute() -> int:\n    return 424242\n",
    ],
)
def test_configuration_rule_does_not_confuse_structural_literals(
    snippet: str, production_payload: str
) -> None:
    assert violations_for_snippet(snippet, production_payload) == []


def test_configuration_value_index_is_nonempty_and_traceable(production_payload: str) -> None:
    values = config_value_index(production_payload)
    assert values
    assert "500" in values
    assert any(path.endswith("bootstrap_resamples") for path in values["500"])
