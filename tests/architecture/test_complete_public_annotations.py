from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.architecture.architecture_rules import (
    missing_public_annotations,
    module_name,
    parse_source,
    production_source_files,
)


def public_annotation_violations(repository_root: Path) -> list[str]:
    violations: list[str] = []
    for source_file in production_source_files(repository_root):
        violations.extend(
            missing_public_annotations(module_name(repository_root, source_file), parse_source(source_file))
        )
    return violations


def snippet_violations(snippet: str) -> list[str]:
    return missing_public_annotations("fedact.example", ast.parse(snippet))


def test_every_public_callable_boundary_is_fully_annotated(repository_root: Path) -> None:
    violations = public_annotation_violations(repository_root)
    assert not violations, "unannotated public boundaries:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    "snippet",
    [
        "def expose(value) -> None:\n    pass\n",
        "def expose(value: int):\n    pass\n",
        "def expose(value, /) -> None:\n    pass\n",
        "def expose(*values) -> None:\n    pass\n",
        "def expose(**values) -> None:\n    pass\n",
        "def expose(*, value) -> None:\n    pass\n",
        "class Service:\n    def expose(self, value) -> None:\n        pass\n",
        "class Service:\n    async def expose(self, value: int):\n        pass\n",
    ],
)
def test_annotation_rule_rejects_every_public_signature_escape(snippet: str) -> None:
    assert snippet_violations(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "def expose(value: int) -> None:\n    pass\n",
        "def expose(value: int, /, *, flag: bool) -> str:\n    return ''\n",
        "def expose(*values: int, **named: str) -> None:\n    pass\n",
        "class Service:\n    def expose(self, value: int) -> None:\n        pass\n",
        "def _private(value) -> None:\n    pass\n",
    ],
)
def test_annotation_rule_accepts_complete_or_private_signatures(snippet: str) -> None:
    assert snippet_violations(snippet) == []
