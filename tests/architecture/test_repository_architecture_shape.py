from __future__ import annotations

from pathlib import Path

import pytest

ALLOWED_TOP_LEVEL_COMPONENTS = frozenset(
    {
        "__init__.py",
        "analysis",
        "app.py",
        "baselines",
        "calibration",
        "cli",
        "config",
        "core",
        "datasets",
        "domain",
        "evaluation",
        "experiments",
        "models",
        "operators",
        "reporting",
        "runtime",
        "scoring",
        "storage",
        "training",
    }
)
REQUIRED_TOP_LEVEL_PACKAGES = frozenset(
    component for component in ALLOWED_TOP_LEVEL_COMPONENTS if not component.endswith(".py")
)
FORBIDDEN_GENERATED_COMPONENTS = frozenset(
    {
        "archive",
        "audits",
        "cache",
        "inventory",
        "roadmap",
        "temp",
        "tmp",
        "outputs",
        "results",
    }
)
ALLOWED_CLI_ROOT_FILES = frozenset({"__init__.py", "main.py"})
REQUIRED_TEST_AREAS = frozenset(
    {"architecture", "integration", "quality", "scientific", "smoke", "unit"}
)


def architecture_shape_violations(repository_root: Path) -> list[str]:
    package_root = repository_root / "src" / "fedact"
    violations: list[str] = []
    if not package_root.is_dir():
        return ["src/fedact package root is missing"]

    present = {path.name for path in package_root.iterdir() if path.name != "__pycache__"}
    unknown = sorted(present - ALLOWED_TOP_LEVEL_COMPONENTS)
    violations.extend(f"unknown top-level production component: {name}" for name in unknown)

    missing = sorted(
        package for package in REQUIRED_TOP_LEVEL_PACKAGES if not (package_root / package).is_dir()
    )
    violations.extend(f"missing production package: {name}" for name in missing)

    for path in package_root.rglob("*"):
        if path.name.lower() in FORBIDDEN_GENERATED_COMPONENTS:
            violations.append(
                f"generated/audit component inside production package: "
                f"{path.relative_to(repository_root).as_posix()}"
            )

    cli_root = package_root / "cli"
    if cli_root.is_dir():
        stray_cli_files = sorted(
            path.name for path in cli_root.glob("*.py") if path.name not in ALLOWED_CLI_ROOT_FILES
        )
        violations.extend(
            f"CLI implementation must live under cli/commands: {name}" for name in stray_cli_files
        )
        if not (cli_root / "commands").is_dir():
            violations.append("src/fedact/cli/commands is missing")

    datasets_root = package_root / "datasets"
    if datasets_root.is_dir():
        for child in datasets_root.iterdir():
            if child.is_dir() and not child.name.startswith("__"):
                python_files = list(child.glob("*.py"))
                if not (child / "__init__.py").is_file():
                    violations.append(f"dataset package lacks __init__.py: {child.name}")
                if len(python_files) > 5:
                    violations.append(
                        f"dataset package is over-fragmented: {child.name} has "
                        f"{len(python_files)} Python files"
                    )

    tests_root = repository_root / "tests"
    if not tests_root.is_dir():
        violations.append("tests directory is missing")
    else:
        missing_test_areas = sorted(
            area for area in REQUIRED_TEST_AREAS if not (tests_root / area).is_dir()
        )
        violations.extend(f"missing test area: tests/{area}" for area in missing_test_areas)
    return violations


def test_repository_shape_enforces_components_not_individual_filenames(
    repository_root: Path,
) -> None:
    violations = architecture_shape_violations(repository_root)
    assert not violations, "repository architecture violations:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    ("relative_path", "content"),
    [
        ("src/fedact/random_junk/__init__.py", ""),
        ("src/fedact/utils.py", ""),
        ("src/fedact/domain/temp/state.py", ""),
        ("src/fedact/domain/inventory/state.py", ""),
        ("src/fedact/cli/shortcut.py", ""),
    ],
)
def test_repository_shape_rejects_known_structural_escape_hatches(
    tmp_path: Path, relative_path: str, content: str
) -> None:
    seed_minimal_valid_tree(tmp_path)
    target = tmp_path / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    assert architecture_shape_violations(tmp_path), relative_path


def test_repository_shape_requires_every_test_area(tmp_path: Path) -> None:
    seed_minimal_valid_tree(tmp_path)
    quality_root = tmp_path / "tests" / "quality"
    quality_root.rmdir()
    violations = architecture_shape_violations(tmp_path)
    assert "missing test area: tests/quality" in violations


def test_new_module_inside_known_component_does_not_require_registry_edit(tmp_path: Path) -> None:
    seed_minimal_valid_tree(tmp_path)
    new_module = tmp_path / "src" / "fedact" / "domain" / "new_semantic_record.py"
    new_module.write_text("", encoding="utf-8")
    assert architecture_shape_violations(tmp_path) == []


def seed_minimal_valid_tree(root: Path) -> None:
    package_root = root / "src" / "fedact"
    package_root.mkdir(parents=True)
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "app.py").write_text("", encoding="utf-8")
    for package in REQUIRED_TOP_LEVEL_PACKAGES:
        directory = package_root / package
        directory.mkdir(parents=True)
        (directory / "__init__.py").write_text("", encoding="utf-8")
    cli_commands = package_root / "cli" / "commands"
    cli_commands.mkdir()
    (cli_commands / "__init__.py").write_text("", encoding="utf-8")
    datasets = package_root / "datasets"
    for dataset in ("ember2024", "lamda", "synthetic"):
        dataset_dir = datasets / dataset
        dataset_dir.mkdir()
        (dataset_dir / "__init__.py").write_text("", encoding="utf-8")
    tests_root = root / "tests"
    for area in REQUIRED_TEST_AREAS:
        (tests_root / area).mkdir(parents=True)
