from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.architecture.architecture_rules import (
    parse_source,
    production_source_files,
    relative_source_path,
    suppression_comment_sites,
)

FORBIDDEN_DIRECT_CALLS = frozenset({"print", "eval", "exec", "compile", "breakpoint"})
SILENT_STATEMENTS = (ast.Pass, ast.Continue)


def import_aliases(tree: ast.Module) -> tuple[set[str], set[str], set[str]]:
    builtins_modules = {"builtins"}
    pdb_modules = {"pdb"}
    forbidden_functions = set(FORBIDDEN_DIRECT_CALLS)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "builtins":
                    builtins_modules.add(alias.asname or alias.name)
                elif alias.name == "pdb":
                    pdb_modules.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "builtins":
            for alias in node.names:
                if alias.name in FORBIDDEN_DIRECT_CALLS:
                    forbidden_functions.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module == "pdb":
            for alias in node.names:
                if alias.name == "set_trace":
                    forbidden_functions.add(alias.asname or alias.name)
    return builtins_modules, pdb_modules, forbidden_functions


def constant_string(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def dynamic_lookup_name(
    node: ast.AST,
    builtins_modules: set[str],
    pdb_modules: set[str],
) -> str | None:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "getattr":
        if len(node.args) >= 2 and isinstance(node.args[0], ast.Name):
            attribute = constant_string(node.args[1])
            if node.args[0].id in builtins_modules and attribute in FORBIDDEN_DIRECT_CALLS:
                return f"{node.args[0].id}.{attribute}"
            if node.args[0].id in pdb_modules and attribute == "set_trace":
                return f"{node.args[0].id}.set_trace"
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        key = constant_string(node.slice)
        if node.value.id == "__builtins__" and key in FORBIDDEN_DIRECT_CALLS:
            return f"__builtins__[{key!r}]"
    return None


def dynamic_call_violations(path: str, tree: ast.Module) -> list[str]:
    builtins_modules, pdb_modules, forbidden_functions = import_aliases(tree)
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id in forbidden_functions:
            violations.append(f"{path}:{node.lineno}: forbidden {node.func.id}()")
            continue
        if isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            if node.func.value.id in builtins_modules and node.func.attr in FORBIDDEN_DIRECT_CALLS:
                violations.append(
                    f"{path}:{node.lineno}: forbidden {node.func.value.id}.{node.func.attr}()"
                )
                continue
            if node.func.value.id in pdb_modules and node.func.attr == "set_trace":
                violations.append(
                    f"{path}:{node.lineno}: forbidden {node.func.value.id}.set_trace()"
                )
                continue
        dynamic_name = dynamic_lookup_name(node.func, builtins_modules, pdb_modules)
        if dynamic_name is not None:
            violations.append(f"{path}:{node.lineno}: forbidden dynamic lookup {dynamic_name}()")
    return violations


def exception_violations(path: str, tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        if node.type is None:
            violations.append(f"{path}:{node.lineno}: bare except is forbidden")
        meaningful: list[ast.stmt] = []
        for statement in node.body:
            if (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            ):
                continue
            meaningful.append(statement)
        if not meaningful:
            violations.append(f"{path}:{node.lineno}: empty exception handler")
            continue
        silent = True
        for statement in meaningful:
            if isinstance(statement, SILENT_STATEMENTS):
                continue
            if (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and statement.value.value is Ellipsis
            ):
                continue
            silent = False
            break
        if silent:
            violations.append(f"{path}:{node.lineno}: silently swallowed exception")
    return violations


def forbidden_pattern_violations(repository_root: Path) -> list[str]:
    violations: list[str] = []
    for source_file in production_source_files(repository_root):
        path = relative_source_path(repository_root, source_file)
        text = source_file.read_text(encoding="utf-8")
        tree = parse_source(source_file)
        violations.extend(dynamic_call_violations(path, tree))
        violations.extend(exception_violations(path, tree))
        violations.extend(suppression_comment_sites(path, text))
    return violations


def snippet_violations(snippet: str) -> list[str]:
    tree = ast.parse(snippet)
    return (
        dynamic_call_violations("example.py", tree)
        + exception_violations("example.py", tree)
        + suppression_comment_sites("example.py", snippet)
    )


def test_production_contains_no_dynamic_debug_suppression_or_silent_exception_patterns(
    repository_root: Path,
) -> None:
    violations = forbidden_pattern_violations(repository_root)
    assert not violations, "forbidden production patterns:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    "snippet",
    [
        "print('debug')\n",
        "eval('1 + 1')\n",
        "exec('value = 1')\n",
        "compile('1 + 1', '<x>', 'eval')\n",
        "breakpoint()\n",
        "import builtins\nbuiltins.eval('1 + 1')\n",
        "import builtins as b\nb.eval('1 + 1')\n",
        "from builtins import eval as e\ne('1 + 1')\n",
        "getattr(__import__('builtins'), 'eval')('1 + 1')\n",
        "import builtins as b\ngetattr(b, 'eval')('1 + 1')\n",
        "__builtins__['eval']('1 + 1')\n",
        "import pdb\npdb.set_trace()\n",
        "import pdb as p\np.set_trace()\n",
        "from pdb import set_trace as trace\ntrace()\n",
        "import pdb as p\ngetattr(p, 'set_trace')()\n",
        "try:\n    work()\nexcept Exception:\n    pass\n",
        "try:\n    work()\nexcept Exception:\n    ...\n",
        "for item in values:\n    try:\n        work(item)\n    except Exception:\n        continue\n",
        "try:\n    work()\nexcept:\n    raise\n",
        "value: int = source  # type: ignore\n",
        "value = source  # noqa: F841\n",
        "value = source  # pyright: ignore[reportAssignmentType]\n",
    ],
)
def test_forbidden_pattern_rule_rejects_known_escape_hatches(snippet: str) -> None:
    assert snippet_violations(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "try:\n    work()\nexcept ValueError as exc:\n    raise RuntimeError('invalid') from exc\n",
        "try:\n    work()\nexcept ValueError:\n    recover()\n",
        "logger.info('ready')\n",
        "import builtins as b\nb.len([1])\n",
    ],
)
def test_forbidden_pattern_rule_accepts_explicit_handling(snippet: str) -> None:
    assert snippet_violations(snippet) == []
