from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.architecture.architecture_rules import (
    parse_source,
    production_source_files,
    relative_source_path,
)

SCALAR_UNWRAP_NAMES = frozenset({"int", "float", "str", "bool"})
JSON_BOUNDARY_TYPE_NAMES = frozenset({"JsonEncodableValue", "JsonValue"})


def _annotation_names(annotation: ast.expr | None) -> set[str]:
    if annotation is None:
        return set()
    return {node.id for node in ast.walk(annotation) if isinstance(node, ast.Name)}


def scalar_unwrap_violations_for_tree(path: str, tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for function in ast.walk(tree):
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        typed_parameters = {
            argument.arg
            for argument in (
                *function.args.posonlyargs,
                *function.args.args,
                *function.args.kwonlyargs,
            )
            if _annotation_names(argument.annotation) - JSON_BOUNDARY_TYPE_NAMES
        }
        for node in ast.walk(function):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in SCALAR_UNWRAP_NAMES
                and len(node.args) == 1
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id in typed_parameters
            ):
                continue
            violations.append(
                f"{path}:{node.lineno}: redundant {node.func.id}() unwrap of {node.args[0].id}"
            )
    return violations


def scalar_unwrap_violations(repository_root: Path) -> list[str]:
    violations: list[str] = []
    for source_file in production_source_files(repository_root):
        violations.extend(
            scalar_unwrap_violations_for_tree(
                relative_source_path(repository_root, source_file), parse_source(source_file)
            )
        )
    return violations


def violations_for_snippet(snippet: str) -> list[str]:
    return scalar_unwrap_violations_for_tree("example.py", ast.parse(snippet))


def test_domain_values_do_not_unwrap_to_primitives_for_internal_calls(
    repository_root: Path,
) -> None:
    violations = scalar_unwrap_violations(repository_root)
    assert not violations, "redundant scalar unwraps:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    "snippet",
    [
        "def run(count: SampleCount) -> None:\n    int(count)\n",
        "def run(rate: MetricRate) -> None:\n    float(rate)\n",
        "def run(path: RelativePosixPath) -> None:\n    str(path)\n",
        "def run(flag: ValidationFlag) -> None:\n    bool(flag)\n",
    ],
)
def test_scalar_unwrap_rule_rejects_domain_unwraps(snippet: str) -> None:
    assert violations_for_snippet(snippet), snippet


def test_scalar_unwrap_rule_accepts_json_numeric_boundary_parsing() -> None:
    snippet = "def parse(value: JsonEncodableValue) -> float:\n    return float(value)\n"
    assert violations_for_snippet(snippet) == []
