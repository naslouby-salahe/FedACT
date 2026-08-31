from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.architecture_rules import (
    annotation_sites,
    module_name,
    parse_source,
    production_source_files,
    relative_source_path,
)

GENERIC_WRAPPER_NAMES = frozenset(
    {
        "PositiveInt",
        "NonNegativeInt",
        "PositiveInteger",
        "NonNegativeInteger",
        "FiniteInt",
        "NonFiniteInt",
        "FiniteFloat",
        "PositiveFloat",
        "NonNegativeFloat",
        "ValidatedFloat",
        "GenericNumber",
        "PositiveIntValue",
        "StrictInteger",
        "StrictBoolean",
    }
)
CONFIGURATION_MODEL_MODULE = "fedact.config.models"


def generic_wrapper_violations_for_tree(module: str, path: str, tree: ast.Module) -> list[str]:
    if module == CONFIGURATION_MODEL_MODULE:
        return []
    violations: list[str] = []
    for site in annotation_sites(module, tree):
        names: set[str] = set()
        for node in ast.walk(site.annotation):
            if isinstance(node, ast.Name):
                names.add(node.id)
        leaked = sorted(names & GENERIC_WRAPPER_NAMES)
        if leaked:
            violations.append(
                f"{path}:{site.lineno}: {site.symbol} {site.kind} uses generic wrapper {leaked}"
            )
    return violations


def generic_wrapper_violations(repository_root: Path) -> list[str]:
    violations: list[str] = []
    for source_file in production_source_files(repository_root):
        module = module_name(repository_root, source_file)
        path = relative_source_path(repository_root, source_file)
        violations.extend(
            generic_wrapper_violations_for_tree(module, path, parse_source(source_file))
        )
    return violations


def test_public_boundaries_do_not_use_generic_numeric_wrappers(repository_root: Path) -> None:
    violations = generic_wrapper_violations(repository_root)
    assert not violations, "generic numeric wrappers:\n" + "\n".join(violations)


def test_generic_wrapper_rule_detects_positive_int_parameter() -> None:
    tree = ast.parse("def run(count: PositiveInt) -> None:\n    return\n")
    violations = generic_wrapper_violations_for_tree("fedact.datasets.splits", "x.py", tree)
    assert violations


def test_generic_wrapper_rule_accepts_semantic_domain_type() -> None:
    tree = ast.parse("def run(count: SampleCount) -> None:\n    return\n")
    assert generic_wrapper_violations_for_tree("fedact.datasets.splits", "x.py", tree) == []
