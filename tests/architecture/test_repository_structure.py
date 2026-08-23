from __future__ import annotations

from pathlib import Path

REGISTERED_PRODUCTION_MODULES: frozenset[str] = frozenset(
    {
        "src/fedact/__init__.py",
        "src/fedact/domain/__init__.py",
        "src/fedact/domain/enums.py",
        "src/fedact/domain/records.py",
        "src/fedact/domain/assumptions.py",
        "src/fedact/domain/operators/__init__.py",
        "src/fedact/domain/operators/contracts.py",
        "src/fedact/domain/operators/enumeration.py",
        "src/fedact/domain/operators/validity.py",
        "src/fedact/datasets/__init__.py",
        "src/fedact/datasets/audits.py",
        "src/fedact/datasets/chronology.py",
        "src/fedact/datasets/preprocessing.py",
        "src/fedact/datasets/records.py",
        "src/fedact/datasets/splits.py",
        "src/fedact/datasets/synthetic/__init__.py",
        "src/fedact/datasets/synthetic/generator.py",
        "src/fedact/datasets/synthetic/geometry.py",
        "src/fedact/datasets/synthetic/validation.py",
        "src/fedact/datasets/lamda/__init__.py",
        "src/fedact/datasets/lamda/semantics.py",
        "src/fedact/datasets/ember2024/__init__.py",
        "src/fedact/datasets/ember2024/semantics.py",
        "src/fedact/models/__init__.py",
        "src/fedact/models/representation.py",
        "src/fedact/models/detector.py",
        "src/fedact/training/__init__.py",
        "src/fedact/training/representation.py",
        "src/fedact/training/detector.py",
        "src/fedact/operators/__init__.py",
        "src/fedact/operators/common.py",
        "src/fedact/operators/lamda.py",
        "src/fedact/operators/ember2024.py",
        "src/fedact/operators/validation.py",
        "src/fedact/scoring/__init__.py",
        "src/fedact/scoring/detector.py",
        "src/fedact/config/__init__.py",
        "src/fedact/config/models.py",
        "src/fedact/config/loading.py",
        "src/fedact/config/validation.py",
        "src/fedact/artifacts/__init__.py",
        "src/fedact/artifacts/identity.py",
        "src/fedact/artifacts/lifecycle.py",
        "src/fedact/artifacts/dependencies.py",
        "src/fedact/artifacts/paths.py",
        "src/fedact/artifacts/provenance.py",
        "src/fedact/runtime/__init__.py",
        "src/fedact/runtime/determinism.py",
        "src/fedact/runtime/environment.py",
        "src/fedact/runtime/logging.py",
        "src/fedact/runtime/planning.py",
        "src/fedact/runtime/state.py",
        "src/fedact/runtime/executor.py",
        "src/fedact/experiments/__init__.py",
        "src/fedact/experiments/definitions.py",
        "src/fedact/experiments/dependencies.py",
        "src/fedact/experiments/registry.py",
        "src/fedact/experiments/producers.py",
        "src/fedact/app.py",
        "src/fedact/cli/__init__.py",
        "src/fedact/cli/main.py",
        "src/fedact/cli/commands/__init__.py",
        "src/fedact/cli/commands/doctor.py",
        "src/fedact/cli/commands/preprocess.py",
        "src/fedact/cli/commands/plan.py",
        "src/fedact/cli/commands/smoke.py",
        "src/fedact/cli/commands/run.py",
        "src/fedact/cli/commands/status.py",
        "src/fedact/cli/commands/report.py",
    }
)


def unregistered_modules(repository_root: Path) -> list[str]:
    package_root = repository_root / "src"
    found = {path.relative_to(repository_root).as_posix() for path in package_root.rglob("*.py")}
    return sorted(found - REGISTERED_PRODUCTION_MODULES)


def stale_registrations(repository_root: Path) -> list[str]:
    package_root = repository_root / "src"
    found = {path.relative_to(repository_root).as_posix() for path in package_root.rglob("*.py")}
    return sorted(REGISTERED_PRODUCTION_MODULES - found)


def registered_roots_exist(repository_root: Path) -> list[str]:
    required_directories = ["configs", "data", "docs", "tests", "tests/architecture"]
    return [
        directory
        for directory in required_directories
        if not (repository_root / directory).exists()
    ]


def test_every_production_module_is_registered_in_the_roadmap_structure(
    repository_root: Path,
) -> None:
    violations = unregistered_modules(repository_root)
    assert not violations, (
        f"unregistered modules violate the roadmap repository structure: {violations}; "
        "register them in tests/architecture/test_repository_structure.py when their owning "
        "roadmap component is implemented"
    )


def test_registry_contains_no_stale_entries(repository_root: Path) -> None:
    stale = stale_registrations(repository_root)
    assert not stale, f"registry references missing modules: {stale}"


def test_roadmap_defined_top_level_components_exist(repository_root: Path) -> None:
    missing = registered_roots_exist(repository_root)
    assert not missing, f"missing roadmap-defined components: {missing}"
