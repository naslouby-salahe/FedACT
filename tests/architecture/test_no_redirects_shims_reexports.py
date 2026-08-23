from __future__ import annotations

import ast
from pathlib import Path


def redirect_module_violations(repository_root: Path) -> list[str]:
    package_root = repository_root / "src"
    violations: list[str] = []
    for source_file in sorted(package_root.rglob("*.py")):
        relative = source_file.relative_to(package_root)
        if source_file.name == "__init__.py":
            continue
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        defines_content = any(
            isinstance(
                node,
                (
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.ClassDef,
                    ast.Assign,
                    ast.AnnAssign,
                    ast.If,
                    ast.Try,
                    ast.With,
                ),
            )
            for node in tree.body
        )
        if not defines_content and tree.body:
            violations.append(f"{relative.as_posix()}: re-export-only or empty redirect module")
    return violations


def test_production_modules_must_define_behavior_not_merely_redirect(
    repository_root: Path,
) -> None:
    violations = redirect_module_violations(repository_root)
    assert not violations, f"redirect/shim modules found: {violations}"
