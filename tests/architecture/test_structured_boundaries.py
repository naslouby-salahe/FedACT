from __future__ import annotations

import ast
from collections import defaultdict
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

EXACT_RAW_MAPPING_ADAPTER_SITES: frozenset[tuple[str, str]] = frozenset()


def structured_issue_names(annotation: ast.expr) -> set[str]:
    issues: set[str] = set()
    if annotation_contains_names(annotation, ANY_NAMES):
        issues.add("Any")
    if annotation_contains_names(annotation, OBJECT_NAMES):
        issues.add("object")
    if annotation_mapping_names(annotation):
        issues.add("mapping")
    return issues


def structured_boundary_violations_for_tree(module: str, tree: ast.Module, path: str) -> list[str]:
    violations: list[str] = []
    for site in annotation_sites(module, tree):
        if (site.symbol, site.kind) in EXACT_RAW_MAPPING_ADAPTER_SITES:
            continue
        any_names = annotation_contains_names(site.annotation, ANY_NAMES)
        object_names = annotation_contains_names(site.annotation, OBJECT_NAMES)
        mappings = annotation_mapping_names(site.annotation)
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


def observed_structured_sites(repository_root: Path) -> dict[tuple[str, str], set[str]]:
    observed: dict[tuple[str, str], set[str]] = defaultdict(set)
    for source_file in production_source_files(repository_root):
        module = module_name(repository_root, source_file)
        for site in annotation_sites(module, parse_source(source_file)):
            observed[(site.symbol, site.kind)] |= structured_issue_names(site.annotation)
    return dict(observed)


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
        "from collections.abc import Mapping\n"
        "def expose(value: Mapping[str, int]) -> None:\n"
        "    pass\n",
        "from collections.abc import MutableMapping\n"
        "def expose(value: list[MutableMapping[str, int]]) -> None:\n"
        "    pass\n",
        "from dataclasses import dataclass\n"
        "@dataclass\n"
        "class Record:\n"
        "    payload: dict[str, int]\n",
        "from pydantic import BaseModel\n"
        "class Record(BaseModel):\n"
        "    payload: list[dict[str, int]]\n",
    ],
)
def test_structured_boundary_rule_rejects_nested_escape_hatches(snippet: str) -> None:
    assert violations_for_snippet(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "from dataclasses import dataclass\n"
        "@dataclass\n"
        "class Payload:\n"
        "    count: int\n"
        "\n"
        "def expose(value: Payload) -> None:\n"
        "    pass\n",
        "class Payload:\n    pass\n\ndef expose(value: list[Payload]) -> None:\n    pass\n",
        "from typing import Protocol\n"
        "class Port(Protocol):\n"
        "    def load(self) -> None:\n"
        "        ...\n",
    ],
)
def test_structured_boundary_rule_accepts_named_payloads(snippet: str) -> None:
    assert violations_for_snippet(snippet) == []


def test_raw_mapping_exemptions_are_exact_real_and_necessary(repository_root: Path) -> None:
    observed = observed_structured_sites(repository_root)
    for symbol, kind in EXACT_RAW_MAPPING_ADAPTER_SITES:
        assert symbol.count(".") >= 3
        assert not symbol.endswith(".*")
        assert kind in {"return", "parameter", "field", "vararg", "kwarg"} or kind.startswith(
            ("parameter:", "field:", "vararg:", "kwarg:")
        )
        assert (symbol, kind) in observed, f"stale structured-boundary exemption: {symbol} {kind}"
        assert observed[(symbol, kind)], (
            f"unnecessary structured-boundary exemption: {symbol} {kind}"
        )
