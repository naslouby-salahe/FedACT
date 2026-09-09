from __future__ import annotations

import ast
from pathlib import Path

from fedact.domain.types import RunnableWorkflowName
from tests.architecture.architecture_rules import parse_source

REQUIRED_COMMANDS = frozenset({"doctor", "preprocess", "plan", "smoke", "run", "status", "report"})


def cli_reachability_violations(repository_root: Path) -> list[str]:
    cli_path = repository_root / "src" / "fedact" / "cli.py"
    workflow_path = repository_root / "src" / "fedact" / "workflow.py"
    if not cli_path.is_file() or not workflow_path.is_file():
        return ["cli.py and workflow.py must exist"]
    tree = parse_source(cli_path)
    commands = {
        decorator.args[0].value
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        for decorator in node.decorator_list
        if isinstance(decorator, ast.Call)
        and isinstance(decorator.func, ast.Attribute)
        and decorator.func.attr == "command"
        and decorator.args
        and isinstance(decorator.args[0], ast.Constant)
        and isinstance(decorator.args[0].value, str)
    }
    violations = [f"cli.py missing command {name}" for name in sorted(REQUIRED_COMMANDS - commands)]
    violations.extend(
        f"cli.py has unexpected command {name}" for name in sorted(commands - REQUIRED_COMMANDS)
    )
    workflow_source = workflow_path.read_text(encoding="utf-8")
    for name in RunnableWorkflowName:
        if name.name not in workflow_source:
            violations.append(f"workflow.py does not dispatch RunnableWorkflowName.{name.name}")
    return violations


def test_public_cli_commands_and_workflows_are_dispatched(repository_root: Path) -> None:
    assert cli_reachability_violations(repository_root) == []


def test_cli_reachability_rejects_missing_or_split_control_surface(tmp_path: Path) -> None:
    root = tmp_path / "src" / "fedact"
    root.mkdir(parents=True)
    (root / "cli.py").write_text("import typer\napp = typer.Typer()\n", encoding="utf-8")
    (root / "workflow.py").write_text("", encoding="utf-8")
    assert cli_reachability_violations(tmp_path)


def test_cli_reachability_accepts_complete_control_surface(repository_root: Path) -> None:
    assert cli_reachability_violations(repository_root) == []
