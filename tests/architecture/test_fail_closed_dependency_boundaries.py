from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.architecture_rules import (
    module_name,
    parse_source,
    production_source_files,
    relative_source_path,
)

PACKAGE_DEPENDENCIES: dict[str, frozenset[str]] = {
    "fedact.domain": frozenset(),
    "fedact.config": frozenset({"fedact.domain"}),
    "fedact.data": frozenset({"fedact.domain", "fedact.config"}),
    "fedact.learning": frozenset({"fedact.domain", "fedact.config", "fedact.data"}),
    "fedact.certification": frozenset(
        {"fedact.domain", "fedact.config", "fedact.data", "fedact.learning"}
    ),
    "fedact.experiments": frozenset(
        {
            "fedact.domain",
            "fedact.config",
            "fedact.data",
            "fedact.learning",
            "fedact.certification",
            "fedact.analysis",
        }
    ),
    "fedact.analysis": frozenset(
        {"fedact.domain", "fedact.config", "fedact.experiments", "fedact.artifacts"}
    ),
    "fedact.artifacts": frozenset({"fedact.domain", "fedact.config"}),
    "fedact.workflow": frozenset(
        {
            "fedact.domain",
            "fedact.config",
            "fedact.data",
            "fedact.learning",
            "fedact.certification",
            "fedact.experiments",
            "fedact.analysis",
            "fedact.artifacts",
        }
    ),
    "fedact.cli": frozenset({"fedact.domain", "fedact.workflow"}),
}


def owner(module: str) -> str | None:
    if module == "fedact":
        return "fedact"
    candidate = ".".join(module.split(".")[:2])
    return candidate if candidate in PACKAGE_DEPENDENCIES else None


def imports(tree: ast.Module) -> set[str]:
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names if alias.name.startswith("fedact"))
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("fedact"):
            result.add(node.module)
    return result


def test_internal_dependency_graph_is_fail_closed(repository_root: Path) -> None:
    violations: list[str] = []
    for source in production_source_files(repository_root):
        importer_owner = owner(module_name(repository_root, source))
        if importer_owner is None or importer_owner == "fedact":
            continue
        for imported in imports(parse_source(source)):
            imported_owner = owner(imported)
            if imported_owner is None:
                continue
            if (
                imported_owner not in {"fedact", importer_owner}
                and imported_owner not in PACKAGE_DEPENDENCIES[importer_owner]
            ):
                location = relative_source_path(repository_root, source)
                violations.append(f"{location}: {importer_owner} may not import {imported_owner}")
    assert not violations, "forbidden dependency edges:\n" + "\n".join(violations)


def test_domain_dependency_policy_rejects_outer_layers() -> None:
    assert "fedact.experiments" not in PACKAGE_DEPENDENCIES["fedact.domain"]
