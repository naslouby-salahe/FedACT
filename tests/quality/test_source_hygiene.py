from __future__ import annotations

import ast
import re
import tokenize
from pathlib import Path

import pytest

TEMPORARY_MARKER_PATTERN = re.compile(
    r"\b(TODO|FIXME|HACK|XXX|WIP|TEMPORARY|PLACEHOLDER)\b",
    re.IGNORECASE,
)
SELF_PATH = "tests/quality/test_source_hygiene.py"


def python_sources(repository_root: Path) -> list[Path]:
    roots = [repository_root / "src", repository_root / "tests"]
    return sorted(
        path
        for root in roots
        for path in root.rglob("*.py")
        if path.relative_to(repository_root).as_posix() != SELF_PATH
    )


def docstring_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if ast.get_docstring(node) is not None:
                violations.append(f"{path}:{getattr(node, 'lineno', 1)}: docstring")
    return violations


def comment_violations(path: Path) -> list[str]:
    violations: list[str] = []
    with path.open("r", encoding="utf-8") as source:
        for token in tokenize.generate_tokens(source.readline):
            if token.type == tokenize.COMMENT:
                violations.append(f"{path}:{token.start[0]}: comment")
    return violations


def temporary_marker_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    with path.open("r", encoding="utf-8") as source:
        for token in tokenize.generate_tokens(source.readline):
            if token.type == tokenize.COMMENT and TEMPORARY_MARKER_PATTERN.search(token.string):
                violations.append(f"{path}:{token.start[0]}: temporary marker")
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and TEMPORARY_MARKER_PATTERN.search(node.value)
        ):
            violations.append(f"{path}:{node.lineno}: temporary marker in string")
    return violations


def placeholder_implementation_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = [
            statement
            for statement in node.body
            if not (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            )
        ]
        if len(body) == 1 and isinstance(body[0], ast.Pass):
            violations.append(f"{path}:{node.lineno}: placeholder pass body in {node.name}")
            continue
        if (
            len(body) == 1
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and body[0].value.value is Ellipsis
        ):
            violations.append(f"{path}:{node.lineno}: placeholder ellipsis body in {node.name}")
            continue
        for statement in body:
            if not isinstance(statement, ast.Raise) or not isinstance(statement.exc, ast.Call):
                continue
            if isinstance(statement.exc.func, ast.Name) and statement.exc.func.id == "NotImplementedError":
                violations.append(f"{path}:{statement.lineno}: NotImplementedError in {node.name}")
    return violations


def source_hygiene_violations(repository_root: Path) -> list[str]:
    violations: list[str] = []
    for source_file in python_sources(repository_root):
        violations.extend(docstring_violations(source_file))
        violations.extend(comment_violations(source_file))
        violations.extend(temporary_marker_violations(source_file))
        if source_file.is_relative_to(repository_root / "src"):
            violations.extend(placeholder_implementation_violations(source_file))
    return violations


def test_python_sources_are_free_of_comments_docstrings_and_temporary_residue(
    repository_root: Path,
) -> None:
    violations = source_hygiene_violations(repository_root)
    assert not violations, "source hygiene violations:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    "snippet",
    [
        "# TODO remove\nvalue = 1\n",
        "value = 'FIXME later'\n",
        "def execute() -> None:\n    pass\n",
        "def execute() -> None:\n    ...\n",
        "def execute() -> None:\n    raise NotImplementedError()\n",
        "def execute() -> None:\n    \"\"\"temporary docs\"\"\"\n    return None\n",
    ],
)
def test_source_hygiene_detectors_reject_known_residue(tmp_path: Path, snippet: str) -> None:
    path = tmp_path / "violating.py"
    path.write_text(snippet, encoding="utf-8")
    violations = (
        docstring_violations(path)
        + comment_violations(path)
        + temporary_marker_violations(path)
        + placeholder_implementation_violations(path)
    )
    assert violations, snippet


def test_source_hygiene_detectors_accept_complete_code(tmp_path: Path) -> None:
    path = tmp_path / "clean.py"
    path.write_text("def execute(value: int) -> int:\n    return value + 1\n", encoding="utf-8")
    assert docstring_violations(path) == []
    assert comment_violations(path) == []
    assert temporary_marker_violations(path) == []
    assert placeholder_implementation_violations(path) == []
