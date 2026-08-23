from __future__ import annotations

import ast
from pathlib import Path

ALLOWED_IMPORTS: dict[str, frozenset[str]] = {
    "fedact.domain": frozenset(),
    "fedact.config": frozenset({"fedact.domain"}),
    "fedact.datasets": frozenset({"fedact.domain", "fedact.config"}),
    "fedact.models": frozenset({"fedact.domain", "fedact.config"}),
    "fedact.training": frozenset(
        {"fedact.domain", "fedact.config", "fedact.datasets", "fedact.models"}
    ),
    "fedact.operators": frozenset({"fedact.domain", "fedact.config"}),
    "fedact.scoring": frozenset(
        {"fedact.domain", "fedact.config", "fedact.datasets", "fedact.models", "fedact.training"}
    ),
    "fedact.artifacts": frozenset({"fedact.domain", "fedact.config"}),
    "fedact.runtime": frozenset(
        {"fedact.domain", "fedact.config", "fedact.artifacts", "fedact.experiments"}
    ),
    "fedact.experiments": frozenset({"fedact.domain", "fedact.config"}),
    "fedact.app": frozenset(
        {
            "fedact.domain",
            "fedact.config",
            "fedact.datasets",
            "fedact.models",
            "fedact.training",
            "fedact.scoring",
            "fedact.artifacts",
            "fedact.runtime",
            "fedact.experiments",
        }
    ),
    "fedact.cli": frozenset(
        {
            "fedact.domain",
            "fedact.config",
            "fedact.datasets",
            "fedact.models",
            "fedact.training",
            "fedact.scoring",
            "fedact.artifacts",
            "fedact.runtime",
            "fedact.experiments",
            "fedact.app",
        }
    ),
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
    best: str = module_name
    best_length = 0
    for candidate in ALLOWED_IMPORTS:
        candidate_parts = candidate.split(".")
        prefix_matches = tuple(parts[: len(candidate_parts)]) == tuple(candidate_parts)
        improves_best = len(candidate_parts) > best_length
        if prefix_matches and improves_best:
            best = candidate
            best_length = len(candidate_parts)
    return best


def boundary_violations(importer_module: str, imported_modules: list[str]) -> list[str]:
    owner = owning_package(importer_module)
    allowed = ALLOWED_IMPORTS.get(owner, DEFAULT_ALLOWED)
    violations: list[str] = []
    for imported in imported_modules:
        imported_owner = owning_package(imported)
        if imported_owner in {owner, "fedact"}:
            continue
        if imported_owner not in allowed:
            violations.append(f"{importer_module}: {owner} may not import {imported_owner}")
    return violations


def package_module_name(repository_root: Path, source_file: Path) -> str:
    relative = source_file.relative_to(repository_root / "src")
    module = str(relative.with_suffix("")).replace("/", ".")
    if module.endswith(".__init__"):
        module = module[: -len(".__init__")]
    return module


def test_package_dependency_directions_follow_the_architecture(
    repository_root: Path,
) -> None:
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
        "fedact.domain.violating: fedact.domain may not import fedact.experiments"
    ]


def test_cli_layer_may_compose_all_packages(tmp_path: Path) -> None:
    allowed_file = tmp_path / "allowed.py"
    allowed_file.write_text(
        "from fedact.app import Application\nfrom fedact.domain.enums import ScientificOutcome\n",
        encoding="utf-8",
    )
    assert boundary_violations("fedact.cli.allowed", internal_imports(allowed_file)) == []
