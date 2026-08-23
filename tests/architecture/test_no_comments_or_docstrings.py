from __future__ import annotations

import ast
import tokenize
from pathlib import Path


def find_docstring_violations(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    violations: list[str] = []
    for node in ast.walk(tree):
        documented = isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        )
        if documented and ast.get_docstring(node) is not None:
            line = getattr(node, "lineno", 1)
            violations.append(f"{path.name}:{line}")
    return violations


def find_comment_violations(path: Path) -> list[str]:
    violations: list[str] = []
    with path.open("r", encoding="utf-8") as source:
        for token in tokenize.generate_tokens(source.readline):
            if token.type == tokenize.COMMENT:
                violations.append(f"{path.name}:{token.start[0]}: {token.string}")
    return violations


def python_sources(repository_root: Path) -> list[Path]:
    roots = [repository_root / "src", repository_root / "tests"]
    return sorted(path for root in roots for path in root.rglob("*.py"))


def test_repository_python_sources_contain_no_comments_or_docstrings(repository_root: Path) -> None:
    violations: list[str] = []
    for source_file in python_sources(repository_root):
        violations.extend(find_docstring_violations(source_file))
        violations.extend(find_comment_violations(source_file))
    assert not violations, f"comments/docstrings must not remain: {violations[:20]}"


def test_documented_fixture_is_detected(tmp_path: Path) -> None:
    documented = tmp_path / "documented.py"
    documented.write_text(
        '"""Module docstring."""\n\n\ndef described():\n    """Function docstring."""\n',
        encoding="utf-8",
    )
    assert len(find_docstring_violations(documented)) == 2


def test_commented_fixture_is_detected(tmp_path: Path) -> None:
    commented = tmp_path / "commented.py"
    commented.write_text("x = 1  # rationale\n", encoding="utf-8")
    assert len(find_comment_violations(commented)) == 1


def test_clean_fixture_passes(tmp_path: Path) -> None:
    clean = tmp_path / "clean.py"
    clean.write_text("x = 1\n", encoding="utf-8")
    assert find_docstring_violations(clean) == []
    assert find_comment_violations(clean) == []
