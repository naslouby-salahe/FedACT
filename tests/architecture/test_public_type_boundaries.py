from __future__ import annotations

import ast
from pathlib import Path


def unannotated_public_boundaries(repository_root: Path) -> list[str]:
    package_root = repository_root / "src"
    violations: list[str] = []
    for source_file in sorted(package_root.rglob("*.py")):
        relative = source_file.relative_to(package_root).as_posix()
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_") and not (
                node.name.startswith("__") and node.name.endswith("__")
            ):
                continue
            if node.name.startswith("__") and node.name.endswith("__"):
                continue
            positional = node.args.args
            if positional and positional[0].arg in {"self", "cls"}:
                positional = positional[1:]
            for argument in [*positional, *node.args.kwonlyargs]:
                if argument.annotation is None:
                    violations.append(
                        f"{relative}:{node.lineno}: {node.name}: {argument.arg} unannotated"
                    )
            if node.returns is None:
                violations.append(
                    f"{relative}:{node.lineno}: {node.name} missing return annotation"
                )
    return violations


def test_every_public_function_boundary_is_fully_annotated(repository_root: Path) -> None:
    violations = unannotated_public_boundaries(repository_root)
    assert not violations, f"unannotated public boundaries found: {violations}"
