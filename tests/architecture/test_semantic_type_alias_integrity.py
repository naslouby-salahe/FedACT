from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.architecture.architecture_rules import (
    ANY_NAMES,
    BARE_PRIMITIVES,
    MAPPING_NAMES,
    OBJECT_NAMES,
    module_name,
    parse_source,
    production_source_files,
    qualified_name,
    relative_source_path,
    terminal_name,
)

SEMANTIC_ALIAS_VALIDATORS = frozenset(
    {
        "Field",
        "StringConstraints",
        "AfterValidator",
        "BeforeValidator",
        "PlainValidator",
        "WrapValidator",
        "Predicate",
        "Len",
        "Ge",
        "Gt",
        "Le",
        "Lt",
        "MinLen",
        "MaxLen",
    }
)


def alias_like(node: ast.expr) -> bool:
    if isinstance(node, (ast.Name, ast.Attribute, ast.Subscript, ast.BinOp)):
        return True
    return isinstance(node, ast.Call) and terminal_name(node.func) == "NewType"


def top_level_aliases(tree: ast.Module) -> dict[str, ast.expr]:
    aliases: dict[str, ast.expr] = {}
    for node in tree.body:
        if isinstance(node, ast.TypeAlias):
            aliases[node.name.id] = node.value
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id[:1].isupper() and alias_like(node.value):
                aliases[target.id] = node.value
            continue
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.value
            and node.target.id[:1].isupper()
            and alias_like(node.value)
        ):
            aliases[node.target.id] = node.value
    return aliases


def annotated_metadata(node: ast.Subscript) -> list[ast.expr]:
    if terminal_name(node.value) != "Annotated":
        return []
    if not isinstance(node.slice, ast.Tuple) or len(node.slice.elts) < 2:
        return []
    return list(node.slice.elts[1:])


def metadata_is_semantic(metadata: list[ast.expr]) -> bool:
    for item in metadata:
        candidate = item.func if isinstance(item, ast.Call) else item
        if terminal_name(candidate) in SEMANTIC_ALIAS_VALIDATORS:
            return True
    return False


def alias_problems(
    annotation: ast.expr,
    aliases: dict[str, ast.expr],
    resolving: frozenset[str] = frozenset(),
) -> set[str]:
    if isinstance(annotation, ast.Name):
        if annotation.id in BARE_PRIMITIVES:
            return {f"bare primitive {annotation.id}"}
        if annotation.id in ANY_NAMES:
            return {"Any"}
        if annotation.id in OBJECT_NAMES:
            return {"object"}
        if annotation.id in MAPPING_NAMES:
            return {f"anonymous mapping {annotation.id}"}
        target = aliases.get(annotation.id)
        if target is None or annotation.id in resolving:
            return set()
        return alias_problems(target, aliases, resolving | {annotation.id})
    if isinstance(annotation, ast.Attribute):
        name = terminal_name(annotation)
        if name in BARE_PRIMITIVES and qualified_name(annotation) in {
            f"builtins.{primitive}" for primitive in BARE_PRIMITIVES
        }:
            return {f"bare primitive {name}"}
        if name in ANY_NAMES:
            return {"Any"}
        if name in OBJECT_NAMES:
            return {"object"}
        if name in MAPPING_NAMES:
            return {f"anonymous mapping {name}"}
        return set()
    if isinstance(annotation, ast.Call):
        if terminal_name(annotation.func) == "NewType":
            return set()
        return set()
    if isinstance(annotation, ast.Subscript):
        if terminal_name(annotation.value) == "Annotated":
            metadata = annotated_metadata(annotation)
            if not metadata_is_semantic(metadata):
                return {"Annotated alias lacks semantic validation metadata"}
            return set()
        problems = alias_problems(annotation.value, aliases, resolving)
        problems |= alias_problems(annotation.slice, aliases, resolving)
        return problems
    if isinstance(annotation, ast.BinOp):
        return alias_problems(annotation.left, aliases, resolving) | alias_problems(
            annotation.right, aliases, resolving
        )
    if isinstance(annotation, ast.Tuple):
        problems: set[str] = set()
        for element in annotation.elts:
            problems |= alias_problems(element, aliases, resolving)
        return problems
    return set()


def alias_integrity_violations_for_tree(module: str, tree: ast.Module, path: str) -> list[str]:
    aliases = top_level_aliases(tree)
    violations: list[str] = []
    for alias_name, expression in aliases.items():
        problems = alias_problems(expression, aliases, frozenset({alias_name}))
        if problems:
            violations.append(
                f"{path}: {module}.{alias_name} is a transparent/unsafe alias: {sorted(problems)}"
            )
    return violations


def alias_integrity_violations(repository_root: Path) -> list[str]:
    violations: list[str] = []
    for source_file in production_source_files(repository_root):
        violations.extend(
            alias_integrity_violations_for_tree(
                module_name(repository_root, source_file),
                parse_source(source_file),
                relative_source_path(repository_root, source_file),
            )
        )
    return violations


def snippet_violations(snippet: str) -> list[str]:
    return alias_integrity_violations_for_tree("fedact.example", ast.parse(snippet), "example.py")


def test_production_type_aliases_are_semantic_not_primitive_disguises(
    repository_root: Path,
) -> None:
    violations = alias_integrity_violations(repository_root)
    assert not violations, "unsafe semantic type aliases:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    "snippet",
    [
        "SampleCount = int\n",
        "type SampleCount = int\n",
        "A = int\nB = A\n",
        "from typing import Any\ntype Payload = list[Any]\n",
        "from collections.abc import Mapping\ntype Payload = Mapping[str, int]\n",
        "type Payload = dict[str, int]\n",
        "type MaybeCount = int | None\n",
        "from typing import Annotated\ntype SampleCount = Annotated[int, 'semantic-looking']\n",
    ],
)
def test_alias_rule_rejects_primitive_and_container_disguises(snippet: str) -> None:
    assert snippet_violations(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "from typing import Annotated\n"
        "from pydantic import Field\n"
        "type SampleCount = Annotated[int, Field(ge=0)]\n",
        "from typing import Annotated\n"
        "from pydantic import Field\n"
        "type Base = Annotated[int, Field(gt=0)]\n"
        "type Count = Base\n",
        "from typing import NewType\nClientIdentifier = NewType('ClientIdentifier', str)\n",
        "from pathlib import Path\ntype FilePath = Path\n",
        "class DomainRecord:\n    pass\ntype Record = DomainRecord\n",
    ],
)
def test_alias_rule_accepts_validated_or_nominal_types(snippet: str) -> None:
    assert snippet_violations(snippet) == []
