from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from fedact import workflow
from fedact.domain.types import DatasetSelector, ExecutableWorkflowName

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


@app.command("doctor") #TODO: should be enum not hardcoded string
def doctor_entry(repository_root: Path = _REPOSITORY_ROOT_OPTION) -> None:
    workflow.run_doctor(repository_root)


@app.command("preprocess") #TODO: should be enum not hardcoded string
def preprocess_entry(
    dataset: Optional[DatasetSelector] = OptionalDatasetArgument,
    overwrite: bool = OverwriteOption,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    workflow.run_preprocess(dataset, overwrite, repository_root)


@app.command("plan") #TODO: should be enum not hardcoded string
def plan_entry(repository_root: Path = _REPOSITORY_ROOT_OPTION) -> None:
    workflow.run_plan(repository_root)


@app.command("smoke") #TODO: should be enum not hardcoded string
def smoke_entry(
    overwrite: bool = OverwriteOption,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    workflow.run_smoke(overwrite, repository_root)


@app.command("run") #TODO: should be enum not hardcoded string
def run_entry(
    workflow_name: ExecutableWorkflowName,
    overwrite: bool = OverwriteOption,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    workflow.run_experiment(workflow_name, overwrite, repository_root)


@app.command("status") #TODO: should be enum not hardcoded string
def status_entry(
    workflow_name: Optional[ExecutableWorkflowName] = OptionalWorkflowArgument,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    workflow.run_status(workflow_name, repository_root)


@app.command("report") #TODO: should be enum not hardcoded string
def report_entry(
    workflow_name: Optional[ExecutableWorkflowName] = OptionalWorkflowArgument,
    overwrite: bool = OverwriteOption,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    workflow.run_report(workflow_name, overwrite, repository_root)


def main() -> None:
    app()
