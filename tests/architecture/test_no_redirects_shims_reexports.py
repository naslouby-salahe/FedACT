from __future__ import annotations

import ast
from pathlib import Path

import pytest


def local_import_bindings(tree: ast.Module) -> set[str]:
    bindings: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            for alias in node.names:
                bindings.add(alias.asname or alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom) and node.module != "__future__":
            for alias in node.names:
                if alias.name == "*":
                    bindings.add("*")
                else:
                    bindings.add(alias.asname or alias.name)
    return bindings


def root_name(node: ast.AST) -> str | None:
    current = node
    while isinstance(current, ast.Attribute):
        current = current.value
    if isinstance(current, ast.Name):
        return current.id
    return None


def simple_forward_argument(node: ast.AST) -> bool:
    if isinstance(node, ast.Name):
        return True
    return isinstance(node, ast.Starred) and isinstance(node.value, ast.Name)


def direct_forward_call(node: ast.AST, imports: set[str]) -> bool:
    if not isinstance(node, ast.Call):
        return False
    called_root = root_name(node.func)
    if called_root not in imports:
        return False
    if not all(simple_forward_argument(argument) for argument in node.args):
        return False
    return all(
        keyword.arg is None and isinstance(keyword.value, ast.Name)
        or keyword.arg is not None and isinstance(keyword.value, ast.Name)
        for keyword in node.keywords
    )


def dynamic_forward_lookup(node: ast.AST, imports: set[str]) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if not isinstance(node.func, ast.Name) or node.func.id != "getattr":
        return False
    if len(node.args) < 2 or not isinstance(node.args[0], ast.Name):
        return False
    return node.args[0].id in imports and isinstance(node.args[1], ast.Name)


def trivial_forward_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    imports: set[str],
) -> bool:
    body = [
        statement
        for statement in node.body
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        )
    ]
    if len(body) != 1:
        return False
    statement = body[0]
    if isinstance(statement, ast.Return) and statement.value is not None:
        return direct_forward_call(statement.value, imports) or dynamic_forward_lookup(
            statement.value, imports
        )
    if isinstance(statement, ast.Expr):
        return direct_forward_call(statement.value, imports)
    return False


def transparent_import_subclass(node: ast.ClassDef, imports: set[str]) -> bool:
    if not node.bases or not all(root_name(base) in imports for base in node.bases):
        return False
    meaningful = [
        statement
        for statement in node.body
        if not (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and isinstance(statement.value.value, str)
        )
    ]
    return all(
        isinstance(statement, ast.Pass)
        or (
            isinstance(statement, ast.Expr)
            and isinstance(statement.value, ast.Constant)
            and statement.value.value is Ellipsis
        )
        for statement in meaningful
    )


def assignment_is_reexport_or_dummy(node: ast.Assign | ast.AnnAssign, imports: set[str]) -> bool:
    if isinstance(node, ast.Assign):
        targets = node.targets
        value = node.value
    else:
        targets = [node.target]
        value = node.value
    target_names = [target.id for target in targets if isinstance(target, ast.Name)]
    if "__all__" in target_names:
        return True
    if value is None:
        return True
    if isinstance(value, (ast.Name, ast.Attribute)) and root_name(value) in imports:
        return True
    return isinstance(value, ast.Constant)


def meaningful_local_behavior(tree: ast.Module, imports: set[str]) -> bool:
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not trivial_forward_function(node, imports):
                return True
            continue
        if isinstance(node, ast.ClassDef):
            if not transparent_import_subclass(node, imports):
                return True
            continue
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            if not assignment_is_reexport_or_dummy(node, imports):
                return True
            continue
        if isinstance(node, (ast.If, ast.Try, ast.With, ast.For, ast.While, ast.Match)):
            return True
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str):
                continue
        if isinstance(node, ast.Pass):
            continue
        return True
    return False


def redirect_violation_for_tree(path: str, tree: ast.Module) -> list[str]:
    imports = local_import_bindings(tree)
    if not imports:
        return []
    if meaningful_local_behavior(tree, imports):
        return []
    return [f"{path}: re-export-only, forwarding, or redirect shim module"]


def redirect_module_violations(repository_root: Path) -> list[str]:
    package_root = repository_root / "src" / "fedact"
    violations: list[str] = []
    for source_file in sorted(package_root.rglob("*.py")):
        if source_file.name == "__init__.py":
            continue
        relative = source_file.relative_to(repository_root).as_posix()
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        violations.extend(redirect_violation_for_tree(relative, tree))
    return violations


def snippet_violations(snippet: str) -> list[str]:
    return redirect_violation_for_tree("example.py", ast.parse(snippet))


def test_production_modules_define_local_behavior_not_redirect_shims(repository_root: Path) -> None:
    violations = redirect_module_violations(repository_root)
    assert not violations, "redirect/shim modules:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    "snippet",
    [
        "from package.core import execute\n",
        "from package.core import execute\nSENTINEL = 1\n",
        "from package.core import execute\nrun = execute\n",
        "from package.core import execute\n__all__ = ['execute']\n",
        "import package.core as core\ndef run(value):\n    return core.execute(value)\n",
        "import package.core as core\nasync def run(value):\n    return core.execute(value)\n",
        "from package.core import Service\nclass LegacyService(Service):\n    pass\n",
        "import package.core as core\ndef __getattr__(name):\n    return getattr(core, name)\n",
        "from package.core import *\n",
    ],
)
def test_redirect_rule_rejects_known_shim_escape_hatches(snippet: str) -> None:
    assert snippet_violations(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "import math\ndef magnitude(value):\n    return math.sqrt(value * value + 1)\n",
        "from package.core import Item\nITEMS = (Item('a'), Item('b'))\n",
        "import package.core as core\ndef run(value):\n    validated = validate(value)\n    return core.execute(validated)\n",
        "from package.core import Service\nclass Adapter(Service):\n    def execute(self, value):\n        return transform(value)\n",
        "VALUE = 1\n",
    ],
)
def test_redirect_rule_accepts_real_local_behavior(snippet: str) -> None:
    assert snippet_violations(snippet) == []
