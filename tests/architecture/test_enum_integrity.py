from __future__ import annotations

import ast
from pathlib import Path


def enum_definitions(repository_root: Path) -> dict[str, str]:
    package_root = repository_root / "src"
    definitions: dict[str, str] = {}
    for source_file in sorted(package_root.rglob("*.py")):
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                bases = [ast.unparse(base) for base in node.bases]
                if any(base.endswith("StrEnum") for base in bases):
                    definitions[node.name] = source_file.relative_to(package_root).as_posix()
    return definitions


def external_references(repository_root: Path) -> dict[str, set[str]]:
    package_root = repository_root / "src"
    references: dict[str, set[str]] = {}
    for source_file in sorted(package_root.rglob("*.py")):
        defining_module = source_file.relative_to(package_root).as_posix()
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        imported_names: set[str] = set()
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("fedact.")
            ):
                imported_names.update(alias.name for alias in node.names)
            elif isinstance(node, ast.Name):
                imported_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                imported_names.add(node.attr)
        for name in imported_names:
            references.setdefault(name, set()).add(defining_module)
    return references


def unused_or_bypassed_enums(repository_root: Path) -> list[str]:
    violations: list[str] = []
    definitions = enum_definitions(repository_root)
    references = external_references(repository_root)
    for enum_name, defining_file in definitions.items():
        referencing_modules = {
            module for module in references.get(enum_name, set()) if module != defining_file
        }
        if not referencing_modules:
            violations.append(f"{defining_file}: enum {enum_name} is never used outside its module")
    return violations


def test_every_domain_enum_is_consumed_by_other_production_modules(
    repository_root: Path,
) -> None:
    violations = unused_or_bypassed_enums(repository_root)
    assert violations == [], f"unused or bypassed enums found: {violations}"
