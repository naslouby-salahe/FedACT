from __future__ import annotations

import ast
from pathlib import Path

from fedact.domain.enums import ExecutableWorkflowName
from tests.architecture.architecture_rules import parse_source


def _string_constants(tree: ast.Module) -> set[str]:
    return {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }


def cli_reachability_violations(repository_root: Path) -> list[str]:
    main_path = repository_root / "src" / "fedact" / "cli" / "main.py"
    run_path = repository_root / "src" / "fedact" / "cli" / "commands" / "run.py"
    commands_root = repository_root / "src" / "fedact" / "cli" / "commands"
    violations: list[str] = []
    main_tree = parse_source(main_path)
    command_names = {
        node.decorator_list[0].args[0].value
        for node in main_tree.body
        if isinstance(node, ast.FunctionDef)
        and node.decorator_list
        and isinstance(node.decorator_list[0], ast.Call)
        and isinstance(node.decorator_list[0].func, ast.Attribute)
        and node.decorator_list[0].func.attr == "command"
        and node.decorator_list[0].args
        and isinstance(node.decorator_list[0].args[0], ast.Constant)
        and isinstance(node.decorator_list[0].args[0].value, str)
    }
    required_commands = {
        "doctor",
        "preprocess",
        "plan",
        "smoke",
        "run",
        "status",
        "report",
    }
    missing_commands = sorted(required_commands - command_names)
    extra_commands = sorted(command_names - required_commands)
    violations.extend(f"cli/main.py missing public command {name}" for name in missing_commands)
    violations.extend(f"cli/main.py extra public command {name}" for name in extra_commands)
    for command in required_commands:
        if not (commands_root / f"{command}.py").is_file():
            violations.append(f"cli/commands/{command}.py is missing")

    run_source = run_path.read_text(encoding="utf-8")
    if "workflow completed:" in run_source:
        violations.append("cli/commands/run.py contains a generic completed fallthrough")
    if (
        "ScientificOutcome.PASS" in run_source
        and "PREPROCESS" in run_source
        and "run_dataset_preprocessing" not in run_source
    ):
        violations.append("cli/commands/run.py preprocess path does not call a real producer")

    referenced = _string_constants(parse_source(run_path))
    for workflow in ExecutableWorkflowName:
        token = workflow.value.replace("-", "_")
        enum_member = workflow.name
        if enum_member not in run_source and workflow.value not in referenced:
            violations.append(
                f"cli/commands/run.py does not dispatch ExecutableWorkflowName.{enum_member}"
            )
        if token == "preprocess" or workflow is ExecutableWorkflowName.PREPROCESS:
            continue
    return violations


def test_public_cli_commands_and_workflows_are_dispatched(repository_root: Path) -> None:
    violations = cli_reachability_violations(repository_root)
    assert not violations, "CLI/runtime reachability violations:\n" + "\n".join(violations)


def test_cli_reachability_rule_detects_generic_fallthrough(tmp_path: Path) -> None:
    root = tmp_path / "src" / "fedact" / "cli"
    commands = root / "commands"
    commands.mkdir(parents=True)
    (root / "main.py").write_text(
        "import typer\n"
        "app = typer.Typer()\n"
        "@app.command('doctor')\n"
        "def doctor_entry() -> None:\n"
        "    return\n",
        encoding="utf-8",
    )
    (commands / "run.py").write_text(
        "def run(workflow: object) -> None:\n    print('workflow completed: leftover')\n",
        encoding="utf-8",
    )
    violations = cli_reachability_violations(tmp_path)
    assert any("generic completed fallthrough" in item for item in violations)


def test_cli_reachability_rule_accepts_complete_command_surface(tmp_path: Path) -> None:
    root = tmp_path / "src" / "fedact" / "cli"
    commands = root / "commands"
    commands.mkdir(parents=True)
    command_names = ["doctor", "preprocess", "plan", "smoke", "run", "status", "report"]
    decorators = "\n".join(
        f"@app.command('{name}')\ndef {name}_entry() -> None:\n    return\n"
        for name in command_names
    )
    (root / "main.py").write_text(
        "import typer\napp = typer.Typer()\n" + decorators, encoding="utf-8"
    )
    for name in command_names:
        (commands / f"{name}.py").write_text("def run() -> None:\n    return\n", encoding="utf-8")
    dispatch = "\n".join(
        f"    ExecutableWorkflowName.{item.name}\n" for item in ExecutableWorkflowName
    )
    (commands / "run.py").write_text(
        "from fedact.domain.enums import ExecutableWorkflowName\n"
        "def run_dataset_preprocessing() -> None:\n    return\n"
        "def run(workflow: ExecutableWorkflowName) -> None:\n"
        f"{dispatch}",
        encoding="utf-8",
    )
    assert cli_reachability_violations(tmp_path) == []
