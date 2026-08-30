from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.architecture.architecture_rules import (
    annotation_sites,
    collect_type_aliases,
    module_name,
    parse_source,
    primitive_names,
    production_source_files,
    relative_source_path,
)


def primitive_violations_for_tree(module: str, tree: ast.Module, path: str) -> list[str]:
    aliases = collect_type_aliases(tree)
    violations: list[str] = []
    for site in annotation_sites(module, tree):
        leaked = primitive_names(site.annotation, aliases)
        if leaked:
            violations.append(
                f"{path}:{site.lineno}: {site.symbol} {site.kind} leaks {sorted(leaked)}"
            )
    return violations


def primitive_violations(repository_root: Path) -> list[str]:
    violations: list[str] = []
    for source_file in production_source_files(repository_root):
        module = module_name(repository_root, source_file)
        path = relative_source_path(repository_root, source_file)
        violations.extend(primitive_violations_for_tree(module, parse_source(source_file), path))
    return violations


def violations_for_snippet(snippet: str) -> list[str]:
    return primitive_violations_for_tree("fedact.example", ast.parse(snippet), "example.py")


def test_public_and_record_boundaries_do_not_leak_bare_primitives(repository_root: Path) -> None:
    violations = primitive_violations(repository_root)
    assert not violations, "primitive leakage across typed boundaries:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    "snippet",
    [
        "def expose(value: int) -> None:\n    pass\n",
        "SampleCount = int\ndef expose(value: SampleCount) -> None:\n    pass\n",
        "A = int\nB = A\ndef expose(value: B) -> None:\n    pass\n",
        "A = int\ndef expose(value: list[A]) -> None:\n    pass\n",
        "A = str\ndef expose(value: A | None) -> None:\n    pass\n",
        "from dataclasses import dataclass\n@dataclass\nclass Record:\n    count: int\n",
        "from pydantic import BaseModel\nclass Record(BaseModel):\n    name: str\n",
        "def expose(*values: int) -> None:\n    pass\n",
        "def expose(**values: float) -> None:\n    pass\n",
        "def expose() -> bool:\n    return True\n",
    ],
)
def test_primitive_rule_rejects_known_escape_hatches(snippet: str) -> None:
    assert violations_for_snippet(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "from typing import Annotated\n"
        "from pydantic import Field\n"
        "type SampleCount = Annotated[int, Field(ge=0)]\n"
        "def expose(value: SampleCount) -> None:\n"
        "    pass\n",
        "from typing import NewType\n"
        "ClientIdentifier = NewType('ClientIdentifier', str)\n"
        "def expose(value: ClientIdentifier) -> None:\n"
        "    pass\n",
        "class DomainValue:\n    pass\ndef expose(value: DomainValue) -> None:\n    pass\n",
    ],
)
def test_primitive_rule_accepts_semantic_types(snippet: str) -> None:
    assert violations_for_snippet(snippet) == []


def test_typer_command_parameters_are_structurally_exempt_not_listed() -> None:
    snippet = (
        "import typer\n"
        "app = typer.Typer()\n"
        "@app.command()\n"
        "def run(overwrite: bool = False) -> None:\n"
        "    pass\n"
    )
    assert violations_for_snippet(snippet) == []


def test_non_command_functions_still_reject_bare_primitive_parameters() -> None:
    snippet = "def run(overwrite: bool = False) -> None:\n    pass\n"
    assert violations_for_snippet(snippet)
