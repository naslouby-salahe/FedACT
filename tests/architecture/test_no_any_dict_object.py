from __future__ import annotations

import ast
from pathlib import Path

PRIMITIVE_KEYED_DICT_PATTERN = ("dict", "dict[str", "dict[int", "dict[float", "dict[bool")
OBJECT_BOUNDARY_ALLOWED_FILES: frozenset[str] = frozenset()
DICT_BOUNDARY_ALLOWED_FILES: frozenset[str] = frozenset({"src/fedact/config/loading.py"})


def collect_annotation_nodes(tree: ast.AST) -> list[ast.expr]:
    annotations: list[ast.expr] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arguments = [*node.args.args, *node.args.kwonlyargs]
            annotations.extend(arg.annotation for arg in arguments if arg.annotation)
            if node.returns:
                annotations.append(node.returns)
        elif isinstance(node, ast.AnnAssign) and node.annotation:
            annotations.append(node.annotation)
    return annotations


def scan_annotations(repository_root: Path, relative_path: Path) -> list[str]:
    source_file = repository_root / relative_path
    tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
    violations: list[str] = []
    for annotation in collect_annotation_nodes(tree):
        rendered = ast.unparse(annotation)
        if rendered == "Any" or ".Any" in rendered:
            violations.append(f"{relative_path.as_posix()}:{annotation.lineno}: {rendered}")
        if rendered == "object" and relative_path.as_posix() not in OBJECT_BOUNDARY_ALLOWED_FILES:
            violations.append(
                f"{relative_path.as_posix()}:{annotation.lineno}: bare object annotation"
            )
    return violations


def scan_anonymous_dicts(repository_root: Path, relative_path: Path) -> list[str]:
    if relative_path.as_posix() in DICT_BOUNDARY_ALLOWED_FILES:
        return []
    source_file = repository_root / relative_path
    tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
    violations: list[str] = []
    for annotation in collect_annotation_nodes(tree):
        rendered = ast.unparse(annotation)
        if rendered.startswith(PRIMITIVE_KEYED_DICT_PATTERN) and (
            "Any" in rendered or "object" in rendered
        ):
            violations.append(
                f"{relative_path.as_posix()}:{annotation.lineno}: anonymous payload ({rendered})"
            )
    return violations


def production_modules(repository_root: Path) -> list[Path]:
    return sorted((repository_root / "src").rglob("*.py"))


def test_production_annotations_contain_no_any_or_unjustified_object(
    repository_root: Path,
) -> None:
    violations: list[str] = []
    for source_file in production_modules(repository_root):
        violations.extend(
            scan_annotations(repository_root, source_file.relative_to(repository_root))
        )
    assert not violations, f"inappropriate Any/object annotations found: {violations}"


def test_public_boundaries_use_typed_payloads_not_anonymous_dicts(
    repository_root: Path,
) -> None:
    violations: list[str] = []
    for source_file in production_modules(repository_root):
        violations.extend(
            scan_anonymous_dicts(repository_root, source_file.relative_to(repository_root))
        )
    assert not violations, f"anonymous dict payloads found: {violations}"


def test_boundary_allowlists_reference_existing_files_and_stay_narrow(
    repository_root: Path,
) -> None:
    assert len(OBJECT_BOUNDARY_ALLOWED_FILES) == 0
    assert len(DICT_BOUNDARY_ALLOWED_FILES) == 1
    for relative in DICT_BOUNDARY_ALLOWED_FILES:
        assert (repository_root / relative).is_file()
