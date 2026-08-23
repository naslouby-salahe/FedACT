from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from fedact.cli.commands import doctor as doctor_command
from fedact.cli.commands import plan as plan_command
from fedact.cli.commands import preprocess as preprocess_command
from fedact.cli.commands import report as report_command
from fedact.cli.commands import run as run_command
from fedact.cli.commands import smoke as smoke_command
from fedact.cli.commands import status as status_command
from fedact.domain.enums import DatasetSelector, ExecutableWorkflowName

app = typer.Typer(
    name="fedact",
    help="FedACT scientific workflow control surface",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)

_REPOSITORY_ROOT_OPTION = typer.Option(
    ".",
    "--repository-root",
    hidden=True,
)

OverwriteOption = typer.Option(False, "--overwrite")
OptionalDatasetArgument = typer.Argument(None)
OptionalWorkflowArgument = typer.Argument(None)


@app.command("doctor")
def doctor_entry(repository_root: Path = _REPOSITORY_ROOT_OPTION) -> None:
    doctor_command.run(repository_root)


@app.command("preprocess")
def preprocess_entry(
    dataset: Optional[DatasetSelector] = OptionalDatasetArgument,
    overwrite: bool = OverwriteOption,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    preprocess_command.run(dataset, overwrite, repository_root)


@app.command("plan")
def plan_entry(repository_root: Path = _REPOSITORY_ROOT_OPTION) -> None:
    plan_command.run(repository_root)


@app.command("smoke")
def smoke_entry(
    overwrite: bool = OverwriteOption,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    smoke_command.run(overwrite, repository_root)


@app.command("run")
def run_entry(
    workflow: ExecutableWorkflowName,
    overwrite: bool = OverwriteOption,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    run_command.run(workflow, overwrite, repository_root)


@app.command("status")
def status_entry(
    workflow: Optional[ExecutableWorkflowName] = OptionalWorkflowArgument,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    status_command.run(workflow, repository_root)


@app.command("report")
def report_entry(
    workflow: Optional[ExecutableWorkflowName] = OptionalWorkflowArgument,
    overwrite: bool = OverwriteOption,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    report_command.run(workflow, overwrite, repository_root)


def main() -> None:
    app()
