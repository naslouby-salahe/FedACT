from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.architecture.architecture_rules import (
    ANY_NAMES,
    OBJECT_NAMES,
    annotation_contains_names,
    annotation_mapping_names,
    annotation_sites,
    module_name,
    parse_source,
    production_source_files,
    relative_source_path,
)

EXACT_RAW_MAPPING_ADAPTERS = frozenset(
    {
        "fedact.config.loading.parse_raw_configuration_mapping",
    }
)


def structured_boundary_violations_for_tree(
    module: str, tree: ast.Module, path: str
) -> list[str]:
    violations: list[str] = []
    for site in annotation_sites(module, tree):
        any_names = annotation_contains_names(site.annotation, ANY_NAMES)
        object_names = annotation_contains_names(site.annotation, OBJECT_NAMES)
        mappings = annotation_mapping_names(site.annotation)
        if site.symbol in EXACT_RAW_MAPPING_ADAPTERS:
            continue
        rendered = ast.unparse(site.annotation)
        if any_names:
            violations.append(
                f"{path}:{site.lineno}: {site.symbol} {site.kind} contains Any ({rendered})"
            )
        if object_names:
            violations.append(
                f"{path}:{site.lineno}: {site.symbol} {site.kind} contains object ({rendered})"
            )
        if mappings:
            violations.append(
                f"{path}:{site.lineno}: {site.symbol} {site.kind} exposes anonymous mapping "
                f"{sorted(mappings)} ({rendered})"
            )
    return violations


def structured_boundary_violations(repository_root: Path) -> list[str]:
    violations: list[str] = []
    for source_file in production_source_files(repository_root):
        violations.extend(
            structured_boundary_violations_for_tree(
                module_name(repository_root, source_file),
                parse_source(source_file),
                relative_source_path(repository_root, source_file),
            )
        )
    return violations


def violations_for_snippet(snippet: str) -> list[str]:
    return structured_boundary_violations_for_tree(
        "fedact.example", ast.parse(snippet), "example.py"
    )


def test_public_boundaries_use_named_typed_payloads(repository_root: Path) -> None:
    violations = structured_boundary_violations(repository_root)
    assert not violations, "untyped or anonymous boundary payloads:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    "snippet",
    [
        "from typing import Any\ndef expose(value: Any) -> None:\n    pass\n",
        "from typing import Any\ndef expose(value: list[Any]) -> None:\n    pass\n",
        "import typing\ndef expose(value: typing.Any | None) -> None:\n    pass\n",
        "def expose(value: object) -> None:\n    pass\n",
        "def expose(value: list[object]) -> None:\n    pass\n",
        "def expose(value: dict[str, int]) -> None:\n    pass\n",
        "def expose(value: dict[str, object]) -> None:\n    pass\n",
        "from collections.abc import Mapping\ndef expose(value: Mapping[str, int]) -> None:\n    pass\n",
        "from collections.abc import MutableMapping\ndef expose(value: list[MutableMapping[str, int]]) -> None:\n    pass\n",
        "from dataclasses import dataclass\n@dataclass\nclass Record:\n    payload: dict[str, int]\n",
        "from pydantic import BaseModel\nclass Record(BaseModel):\n    payload: list[dict[str, int]]\n",
    ],
)
def test_structured_boundary_rule_rejects_nested_escape_hatches(snippet: str) -> None:
    assert violations_for_snippet(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "from dataclasses import dataclass\n@dataclass\nclass Payload:\n    count: int\n\ndef expose(value: Payload) -> None:\n    pass\n",
        "class Payload:\n    pass\n\ndef expose(value: list[Payload]) -> None:\n    pass\n",
        "from typing import Protocol\nclass Port(Protocol):\n    def load(self) -> None:\n        ...\n",
    ],
)
def test_structured_boundary_rule_accepts_named_payloads(snippet: str) -> None:
    assert violations_for_snippet(snippet) == []


def test_raw_mapping_exemptions_are_exact_adapter_symbols() -> None:
    assert EXACT_RAW_MAPPING_ADAPTERS
    assert all(symbol.count(".") >= 3 for symbol in EXACT_RAW_MAPPING_ADAPTERS)
    assert all(not symbol.endswith(".*") for symbol in EXACT_RAW_MAPPING_ADAPTERS)
