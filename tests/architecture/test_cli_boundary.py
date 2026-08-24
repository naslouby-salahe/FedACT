from __future__ import annotations

import ast
from pathlib import Path

import pytest

SCIENTIFIC_EXTERNAL_ROOTS = frozenset(
    {
        "cvxpy",
        "duckdb",
        "numpy",
        "pandas",
        "polars",
        "scipy",
        "sklearn",
        "torch",
    }
)
SAFE_CLI_INTEGER_LITERALS = frozenset({0, 1, 2})


def is_safe_cli_numeric(node: ast.Constant) -> bool:
    return (
        isinstance(node.value, int)
        and not isinstance(node.value, bool)
        and node.value in SAFE_CLI_INTEGER_LITERALS
    )


def cli_tree_violations(path: str, tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".", 1)[0]
                if root in SCIENTIFIC_EXTERNAL_ROOTS:
                    violations.append(
                        f"{path}:{node.lineno}: CLI imports scientific library {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".", 1)[0]
            if root in SCIENTIFIC_EXTERNAL_ROOTS:
                violations.append(
                    f"{path}:{node.lineno}: CLI imports scientific library {node.module}"
                )
        elif isinstance(node, ast.ClassDef):
            violations.append(f"{path}:{node.lineno}: CLI defines class {node.name}")
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                continue
            if is_safe_cli_numeric(node):
                continue
            violations.append(
                f"{path}:{node.lineno}: CLI embeds numeric/scientific literal {node.value!r}"
            )
    return violations


def cli_boundary_violations(repository_root: Path) -> list[str]:
    cli_root = repository_root / "src" / "fedact" / "cli"
    violations: list[str] = []
    for source_file in sorted(cli_root.rglob("*.py")):
        relative = source_file.relative_to(repository_root).as_posix()
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        violations.extend(cli_tree_violations(relative, tree))
    return violations


def snippet_violations(snippet: str) -> list[str]:
    return cli_tree_violations("cli_example.py", ast.parse(snippet))


def test_cli_contains_only_parsing_validation_invocation_and_rendering(repository_root: Path) -> None:
    violations = cli_boundary_violations(repository_root)
    assert not violations, "CLI boundary violations:\n" + "\n".join(violations)


@pytest.mark.parametrize(
    "snippet",
    [
        "import numpy as np\n",
        "from torch import Tensor\n",
        "class ScientificRunner:\n    pass\n",
        "THRESHOLD = 0.95\n",
        "def run() -> None:\n    evaluate(0.95)\n",
        "DATASET_MONTHS = (0, 143)\n",
        "def run() -> None:\n    evaluate(10.0, 1.0)\n",
    ],
)
def test_cli_rule_rejects_scientific_logic_escape_hatches(snippet: str) -> None:
    assert snippet_violations(snippet), snippet


@pytest.mark.parametrize(
    "snippet",
    [
        "import typer\ndef run() -> None:\n    raise typer.Exit(code=0)\n",
        "import typer\ndef run() -> None:\n    raise typer.Exit(code=1)\n",
        "from fedact.app import Application\ndef run(app: Application) -> None:\n    app.plan()\n",
        "def render(value: object) -> None:\n    print_value(value)\n",
    ],
)
def test_cli_rule_accepts_control_surface_code(snippet: str) -> None:
    assert snippet_violations(snippet) == []
