from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

from tests.architecture.architecture_rules import (
    module_name,
    parse_source,
    production_source_files,
    relative_source_path,
)


def _imported_fedact_modules(tree: ast.Module) -> set[str]:
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "fedact" or alias.name.startswith("fedact."):
                    imported.add(alias.name)
        elif (
            isinstance(node, ast.ImportFrom)
            and node.module is not None
            and (node.module == "fedact" or node.module.startswith("fedact."))
        ):
            imported.add(node.module)
            for alias in node.names:
                if alias.name != "*":
                    imported.add(f"{node.module}.{alias.name}")
    return imported


def _package_modules(repository_root: Path) -> dict[str, str]:
    return {
        module_name(repository_root, source_file): relative_source_path(
            repository_root, source_file
        )
        for source_file in production_source_files(repository_root)
    }


def unreachable_production_module_violations(repository_root: Path) -> list[str]:
    package_modules = _package_modules(repository_root)
    production_imports: dict[str, set[str]] = defaultdict(set)
    for source_file in production_source_files(repository_root):
        importer = module_name(repository_root, source_file)
        for imported in _imported_fedact_modules(parse_source(source_file)):
            production_imports[imported].add(importer)

    test_imports: set[str] = set()
    tests_root = repository_root / "tests"
    for source_file in tests_root.rglob("*.py"):
        test_imports |= _imported_fedact_modules(parse_source(source_file))

    violations: list[str] = []
    for module, path in sorted(package_modules.items()):
        if module in {"fedact", "fedact.cli.main", "fedact.app"}:
            continue
        producers = production_imports.get(module, set()) - {module}
        referenced_by_child = any(
            imported == module or imported.startswith(f"{module}.")
            for imported in production_imports
            if imported != module
        )
        if producers or referenced_by_child:
            continue
        if any(
            imported == module or module.startswith(f"{imported}.") for imported in test_imports
        ):
            violations.append(f"{path}: production module referenced only by tests")
        else:
            parent, _, _child = module.rpartition(".")
            parent_imports_child = False
            parent_source = (repository_root / "src" / "/".join(parent.split("."))).with_suffix(
                ".py"
            )
            if not parent_source.is_file():
                parent_source = (
                    repository_root / "src" / "/".join(parent.split(".")) / "__init__.py"
                )
            if parent_source.is_file():
                parent_imports_child = module in _imported_fedact_modules(
                    parse_source(parent_source)
                )
            if not parent_imports_child:
                violations.append(
                    f"{path}: production module is unreachable from production imports"
                )
    return violations


def test_production_modules_are_reachable_from_application_not_only_tests(
    repository_root: Path,
) -> None:
    violations = unreachable_production_module_violations(repository_root)
    assert not violations, "test-only or unreachable production modules:\n" + "\n".join(violations)


def test_test_only_rule_detects_module_imported_only_from_tests(tmp_path: Path) -> None:
    package = tmp_path / "src" / "fedact"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "orphan.py").write_text("VALUE = 1\n", encoding="utf-8")
    tests = tmp_path / "tests" / "unit"
    tests.mkdir(parents=True)
    (tests / "test_orphan.py").write_text("from fedact.orphan import VALUE\n", encoding="utf-8")
    violations = unreachable_production_module_violations(tmp_path)
    assert any("orphan.py" in item for item in violations)


def test_test_only_rule_accepts_module_imported_from_production(tmp_path: Path) -> None:
    package = tmp_path / "src" / "fedact"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("from fedact.used import VALUE\n", encoding="utf-8")
    (package / "used.py").write_text("VALUE = 1\n", encoding="utf-8")
    (package / "app.py").write_text("from fedact.used import VALUE\n", encoding="utf-8")
    tests = tmp_path / "tests"
    tests.mkdir()
    assert unreachable_production_module_violations(tmp_path) == []
