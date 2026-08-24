from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.architecture.architecture_rules import (
    ImportEdge,
    module_name,
    parse_source,
    production_source_files,
    relative_source_path,
    resolve_relative_import,
)

PACKAGE_DEPENDENCIES: dict[str, frozenset[str]] = {
    "fedact.domain": frozenset(),
    "fedact.config": frozenset({"fedact.domain"}),
    "fedact.datasets": frozenset({"fedact.domain", "fedact.config"}),
    "fedact.models": frozenset({"fedact.domain", "fedact.config"}),
    "fedact.training": frozenset(
        {"fedact.domain", "fedact.config", "fedact.datasets", "fedact.models"}
    ),
    "fedact.operators": frozenset({"fedact.domain", "fedact.config"}),
    "fedact.fedact": frozenset({"fedact.domain", "fedact.config"}),
    "fedact.scoring": frozenset(
        {"fedact.domain", "fedact.config", "fedact.datasets", "fedact.models", "fedact.training"}
    ),
    "fedact.artifacts": frozenset({"fedact.domain", "fedact.config"}),
    "fedact.baselines": frozenset(
        {"fedact.domain", "fedact.config", "fedact.models", "fedact.training", "fedact.scoring"}
    ),
    "fedact.calibration": frozenset(
        {"fedact.domain", "fedact.config", "fedact.datasets", "fedact.models", "fedact.fedact"}
    ),
    "fedact.evaluation": frozenset(
        {
            "fedact.domain",
            "fedact.config",
            "fedact.datasets",
            "fedact.models",
            "fedact.scoring",
            "fedact.operators",
            "fedact.fedact",
            "fedact.baselines",
        }
    ),
    "fedact.analysis": frozenset({"fedact.domain", "fedact.config", "fedact.evaluation"}),
    "fedact.reporting": frozenset(
        {
            "fedact.domain",
            "fedact.config",
            "fedact.evaluation",
            "fedact.analysis",
            "fedact.artifacts",
        }
    ),
    "fedact.runtime": frozenset(
        {"fedact.domain", "fedact.config", "fedact.artifacts", "fedact.experiments"}
    ),
    "fedact.experiments": frozenset(
        {
            "fedact.domain",
            "fedact.config",
            "fedact.datasets",
            "fedact.models",
            "fedact.training",
            "fedact.scoring",
            "fedact.operators",
            "fedact.fedact",
            "fedact.baselines",
            "fedact.calibration",
            "fedact.evaluation",
            "fedact.analysis",
            "fedact.artifacts",
        }
    ),
    "fedact.app": frozenset(
        {
            "fedact.domain",
            "fedact.config",
            "fedact.datasets",
            "fedact.models",
            "fedact.training",
            "fedact.scoring",
            "fedact.operators",
            "fedact.fedact",
            "fedact.baselines",
            "fedact.calibration",
            "fedact.evaluation",
            "fedact.analysis",
            "fedact.artifacts",
            "fedact.reporting",
            "fedact.runtime",
            "fedact.experiments",
        }
    ),
    "fedact.cli": frozenset({"fedact.app"}),
}


def owner(module: str) -> str | None:
    if module == "fedact":
        return "fedact"
    parts = module.split(".")
    if len(parts) < 2 or parts[0] != "fedact":
        return None
    candidate = ".".join(parts[:2])
    return candidate if candidate in PACKAGE_DEPENDENCIES else None


def edges_for_tree(importer: str, tree: ast.Module) -> list[ImportEdge]:
    edges: list[ImportEdge] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "fedact" or alias.name.startswith("fedact."):
                    edges.append(ImportEdge(importer, alias.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = resolve_relative_import(importer, node.level, node.module)
                if not base:
                    edges.append(ImportEdge(importer, "<invalid-relative-import>", node.lineno))
                elif node.module is None:
                    for alias in node.names:
                        if alias.name != "*":
                            edges.append(
                                ImportEdge(importer, f"{base}.{alias.name}", node.lineno)
                            )
                else:
                    edges.append(ImportEdge(importer, base, node.lineno))
            elif node.module == "fedact":
                for alias in node.names:
                    if alias.name != "*":
                        edges.append(
                            ImportEdge(importer, f"fedact.{alias.name}", node.lineno)
                        )
            elif node.module and node.module.startswith("fedact."):
                edges.append(ImportEdge(importer, node.module, node.lineno))
    return edges


def dependency_violations_for_tree(
    importer: str, tree: ast.Module, path: str
) -> list[str]:
    importer_owner = owner(importer)
    if importer_owner is None:
        return [f"{path}: unknown architectural package owner for {importer}"]
    if importer_owner == "fedact":
        return []
    allowed = PACKAGE_DEPENDENCIES[importer_owner]
    violations: list[str] = []
    for edge in edges_for_tree(importer, tree):
        imported_owner = owner(edge.imported)
        if imported_owner is None:
            violations.append(
                f"{path}:{edge.lineno}: {importer_owner} imports unknown internal package "
                f"{edge.imported}"
            )
            continue
        if imported_owner in {importer_owner, "fedact"}:
            continue
        if imported_owner not in allowed:
            violations.append(
                f"{path}:{edge.lineno}: {importer_owner} may not import {imported_owner}"
            )
    return violations


def dependency_violations(repository_root: Path) -> list[str]:
    violations: list[str] = []
    for source_file in production_source_files(repository_root):
        violations.extend(
            dependency_violations_for_tree(
                module_name(repository_root, source_file),
                parse_source(source_file),
                relative_source_path(repository_root, source_file),
            )
        )
    return violations


def violations_for_snippet(importer: str, snippet: str) -> list[str]:
    return dependency_violations_for_tree(importer, ast.parse(snippet), "example.py")


def test_internal_dependency_graph_is_fail_closed(repository_root: Path) -> None:
    violations = dependency_violations(repository_root)
    assert not violations, "forbidden or unknown dependency edges:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    ("importer", "snippet"),
    [
        ("fedact.domain.example", "from fedact.experiments import registry\n"),
        ("fedact.domain.example", "from fedact import experiments\n"),
        ("fedact.domain.example", "from ..experiments import registry\n"),
        ("fedact.domain.example", "import fedact.random_junk.module\n"),
        ("fedact.random_junk.example", "from fedact.domain import records\n"),
        ("fedact.cli.example", "from fedact.domain import enums\n"),
        ("fedact.cli.example", "from fedact.experiments import registry\n"),
    ],
)
def test_dependency_rule_rejects_known_escape_hatches(
    importer: str, snippet: str
) -> None:
    assert violations_for_snippet(importer, snippet), (importer, snippet)


@pytest.mark.parametrize(
    ("importer", "snippet"),
    [
        ("fedact.config.example", "from fedact.domain import enums\n"),
        ("fedact.domain.example", "from . import records\n"),
        ("fedact.domain.example", "from fedact.domain import types\n"),
        ("fedact.cli.example", "from fedact.app import Application\n"),
    ],
)
def test_dependency_rule_accepts_declared_edges(importer: str, snippet: str) -> None:
    assert violations_for_snippet(importer, snippet) == []


def test_every_declared_package_has_explicit_dependency_policy() -> None:
    assert PACKAGE_DEPENDENCIES
    assert "fedact.domain" in PACKAGE_DEPENDENCIES
    assert "fedact.cli" in PACKAGE_DEPENDENCIES
    assert all(package.startswith("fedact.") for package in PACKAGE_DEPENDENCIES)
