from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.architecture.architecture_rules import (
    module_name,
    parse_source,
    production_source_files,
    relative_source_path,
)

FORBIDDEN_GENERIC_ALIASES = frozenset(
    {
        "NonNegativeInt",
        "PositiveInt",
        "NonNegativeFloat",
        "PositiveFloat",
        "UnitInterval",
        "OpenUnitInterval",
        "FiniteFloat",
        "SignedInt",
    }
)
CANONICAL_TYPE_MODULE = "fedact.domain.types"


def forbidden_alias_violations_for_tree(module: str, path: str, tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_GENERIC_ALIASES:
            violations.append(f"{path}:{node.lineno}: forbidden generic alias {node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_GENERIC_ALIASES:
            violations.append(
                f"{path}:{node.lineno}: forbidden generic alias attribute {node.attr}"
            )
    return violations


def forbidden_alias_violations(repository_root: Path) -> list[str]:
    violations: list[str] = []
    for source_file in production_source_files(repository_root):
        module = module_name(repository_root, source_file)
        if module == CANONICAL_TYPE_MODULE:
            continue
        path = relative_source_path(repository_root, source_file)
        tree = parse_source(source_file)
        violations.extend(forbidden_alias_violations_for_tree(module, path, tree))
    return violations


def snippet_violations(snippet: str) -> list[str]:
    return forbidden_alias_violations_for_tree("fedact.example", "example.py", ast.parse(snippet))


def test_generic_aliases_are_confined_to_canonical_types_module(repository_root: Path) -> None:
    violations = forbidden_alias_violations(repository_root)
    assert not violations, "forbidden generic aliases outside domain/types.py:\n" + "\n".join(
        violations
    )


@pytest.mark.parametrize(
    "snippet",
    [
        "def run(count: PositiveInt) -> None:\n    pass\n",
        (
            "from fedact.domain.types import NonNegativeInt\n"
            "def run(count: NonNegativeInt) -> None:\n    pass\n"
        ),
        "def run(values: list[FiniteFloat]) -> None:\n    pass\n",
        "type MaybeUnit = UnitInterval | None\n",
        "PositiveInt = int\ndef run(count: PositiveInt) -> None:\n    pass\n",
    ],
)
def test_forbidden_alias_rule_rejects_known_escape_hatches(snippet: str) -> None:
    assert snippet_violations(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "def run(count: SampleCount) -> None:\n    pass\n",
        "def run(seed: SeedValue) -> None:\n    pass\n",
        (
            "from fedact.domain.types import ClientCount\n"
            "def run(count: ClientCount) -> None:\n    pass\n"
        ),
    ],
)
def test_forbidden_alias_rule_accepts_domain_types(snippet: str) -> None:
    assert snippet_violations(snippet) == []
