from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

SNAKE_CASE_PATTERN = re.compile(r"^_?[a-z][a-z0-9_]*$")
PASCAL_CASE_PATTERN = re.compile(r"^_?[A-Z][A-Za-z0-9]*$")
FORBIDDEN_PLACEHOLDER_NAMES = frozenset(
    {
        "bar",
        "baz",
        "data2",
        "do_it",
        "foo",
        "handle",
        "helper",
        "helpers",
        "manager",
        "misc",
        "processor",
        "stuff",
        "temp",
        "tmp",
        "util",
        "utils",
    }
)


def checked_identifier(name: str, kind: str, lineno: int, path: str) -> list[str]:
    violations: list[str] = []
    normalized = name.lower()
    if normalized in FORBIDDEN_PLACEHOLDER_NAMES:
        violations.append(f"{path}:{lineno}: {kind} uses placeholder name {name}")
    return violations


class NamingVisitor(ast.NodeVisitor):
    def __init__(self, path: str) -> None:
        self.path = path
        self.function_depth = 0
        self.violations: list[str] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if not PASCAL_CASE_PATTERN.fullmatch(node.name):
            self.violations.append(
                f"{self.path}:{node.lineno}: class {node.name} violates PascalCase"
            )
        self.violations.extend(checked_identifier(node.name, "class", node.lineno, self.path))
        self.generic_visit(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        if not (node.name.startswith("__") and node.name.endswith("__")):
            if not SNAKE_CASE_PATTERN.fullmatch(node.name):
                self.violations.append(
                    f"{self.path}:{node.lineno}: function {node.name} violates snake_case"
                )
            self.violations.extend(
                checked_identifier(node.name, "function", node.lineno, self.path)
            )
        arguments = [
            *node.args.posonlyargs,
            *node.args.args,
            *node.args.kwonlyargs,
        ]
        if node.args.vararg is not None:
            arguments.append(node.args.vararg)
        if node.args.kwarg is not None:
            arguments.append(node.args.kwarg)
        for argument in arguments:
            if argument.arg in {"self", "cls"}:
                continue
            if not SNAKE_CASE_PATTERN.fullmatch(argument.arg):
                self.violations.append(
                    f"{self.path}:{argument.lineno}: parameter {argument.arg} violates snake_case"
                )
            self.violations.extend(
                checked_identifier(argument.arg, "parameter", argument.lineno, self.path)
            )
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            self.violations.extend(checked_identifier(node.id, "variable", node.lineno, self.path))
            if self.function_depth and not SNAKE_CASE_PATTERN.fullmatch(node.id):
                self.violations.append(
                    f"{self.path}:{node.lineno}: local variable {node.id} violates snake_case"
                )
        self.generic_visit(node)

    def visit_alias(self, node: ast.alias) -> None:
        if node.asname:
            self.violations.extend(checked_identifier(node.asname, "import alias", 1, self.path))
            if not SNAKE_CASE_PATTERN.fullmatch(node.asname):
                self.violations.append(
                    f"{self.path}:1: import alias {node.asname} violates snake_case"
                )
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.name:
            self.violations.extend(
                checked_identifier(node.name, "exception variable", node.lineno, self.path)
            )
            if not SNAKE_CASE_PATTERN.fullmatch(node.name):
                self.violations.append(
                    f"{self.path}:{node.lineno}: exception variable {node.name} violates snake_case"
                )
        self.generic_visit(node)


def naming_violations_for_tree(path: str, tree: ast.Module) -> list[str]:
    visitor = NamingVisitor(path)
    visitor.visit(tree)
    return visitor.violations


def naming_violations(repository_root: Path) -> list[str]:
    package_root = repository_root / "src" / "fedact"
    violations: list[str] = []
    for source_file in sorted(package_root.rglob("*.py")):
        relative = source_file.relative_to(repository_root).as_posix()
        if source_file.name != "__init__.py" and not SNAKE_CASE_PATTERN.fullmatch(source_file.stem):
            violations.append(f"{relative}: module name violates snake_case")
        if source_file.stem.lower() in FORBIDDEN_PLACEHOLDER_NAMES:
            violations.append(f"{relative}: module uses placeholder name {source_file.stem}")
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        violations.extend(naming_violations_for_tree(relative, tree))
    return violations


def snippet_violations(snippet: str) -> list[str]:
    return naming_violations_for_tree("example.py", ast.parse(snippet))


def test_production_identifiers_follow_enforceable_naming_contract(repository_root: Path) -> None:
    violations = naming_violations(repository_root)
    assert not violations, "naming contract violations:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    "snippet",
    [
        "class bad_class:\n    pass\n",
        "def BadFunction() -> None:\n    pass\n",
        "def execute(BadParameter: int) -> None:\n    pass\n",
        "def execute() -> None:\n    BadLocal = 1\n",
        "def execute(foo: int) -> None:\n    pass\n",
        "def execute(value: int) -> None:\n    tmp = value\n",
        "import numpy as BadAlias\n",
        "try:\n    work()\nexcept ValueError as BadError:\n    raise\n",
    ],
)
def test_naming_rule_rejects_case_and_placeholder_escape_hatches(snippet: str) -> None:
    assert snippet_violations(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "class DomainRecord:\n    pass\n",
        "def compute_interval(sample_count: int) -> None:\n    local_value = sample_count\n",
        "import numpy as np\n",
        "def compute(x: int, y: int) -> int:\n    result = x + y\n    return result\n",
    ],
)
def test_naming_rule_accepts_conventional_and_scientific_names(snippet: str) -> None:
    assert snippet_violations(snippet) == []
