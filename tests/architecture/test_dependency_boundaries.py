from __future__ import annotations

import ast
from pathlib import Path

ALLOWED_IMPORTS: dict[str, frozenset[str]] = {
    "fedact.domain": frozenset(),
    "fedact.config": frozenset({"fedact.domain"}),
    "fedact.artifacts": frozenset({"fedact.domain", "fedact.config"}),
    "fedact.runtime": frozenset({"fedact.domain", "fedact.config", "fedact.artifacts"}),
    "fedact.experiments": frozenset({"fedact.domain", "fedact.config"}),
}
DEFAULT_ALLOWED: frozenset[str] = frozenset(ALLOWED_IMPORTS)


def internal_imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.append(node.module)
    return [module for module in modules if module == "fedact" or module.startswith("fedact.")]


def owning_package(module_name: str) -> str:
    parts = module_name.split(".")
    for candidate in sorted(ALLOWED_IMPORTS, key=len, reverse=True):
        candidate_parts = candidate.split(".")
        if tuple(parts[: len(candidate_parts)]) == tuple(candidate_parts):
            return candidate
    return module_name


def boundary_violations(importer_module: str, imported_modules: list[str]) -> list[str]:
    owner = owning_package(importer_module)
    allowed = ALLOWED_IMPORTS.get(owner, DEFAULT_ALLOWED)
    violations: list[str] = []
    for imported in imported_modules:
        imported_owner = owning_package(imported)
        if imported_owner in {owner, "fedact"}:
            continue
        if imported_owner not in allowed:
            violations.append(
                f"{importer_module}: {owner} may not import {imported_owner} ({imported})"
            )
    return violations


def package_module_name(repository_root: Path, source_file: Path) -> str:
    relative = source_file.relative_to(repository_root / "src")
    module = str(relative.with_suffix("")).replace("/", ".")
    if module.endswith(".__init__"):
        module = module[: -len(".__init__")]
    return module


def test_package_dependency_directions_follow_the_architecture(repository_root: Path) -> None:
    package_root = repository_root / "src" / "fedact"
    violations: list[str] = []
    for source_file in sorted(package_root.rglob("*.py")):
        importer = package_module_name(repository_root, source_file)
        violations.extend(boundary_violations(importer, internal_imports(source_file)))
    assert not violations, f"forbidden dependency directions found: {violations}"


def test_domain_importing_another_package_is_detected(tmp_path: Path) -> None:
    violating = tmp_path / "violating.py"
    violating.write_text(
        "from fedact.experiments.dependencies import WORKFLOW_ORDER\n", encoding="utf-8"
    )
    violations = boundary_violations("fedact.domain.violating", internal_imports(violating))
    assert violations == [
        "fedact.domain.violating: fedact.domain may not import fedact.experiments "
        "(fedact.experiments.dependencies)"
    ]


def test_experiments_importing_domain_and_config_is_allowed(tmp_path: Path) -> None:
    allowed_file = tmp_path / "allowed.py"
    allowed_file.write_text(
        "from fedact.domain.enums import WorkflowName\n"
        "from fedact.config.models import FedActConfig\n",
        encoding="utf-8",
    )
    assert boundary_violations("fedact.experiments.allowed", internal_imports(allowed_file)) == []
