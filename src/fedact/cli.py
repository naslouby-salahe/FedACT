from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from fedact import workflow
from fedact.domain.types import (
    ByteBudget,
    CliCommandName,
    DatasetSelector,
    ExecutableWorkflowName,
)

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
MaximumTotalBytesOption = typer.Option(
    ...,
    "--maximum-total-bytes",
    help="Byte budget for this run; acquisition stops once newly downloaded bytes reach it.",
)
OptionalDatasetArgument = typer.Argument(None)
OptionalWorkflowArgument = typer.Argument(None)


@app.command(CliCommandName.ACQUIRE)
def acquire_entry(
    maximum_total_bytes: int = MaximumTotalBytesOption,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    workflow.run_acquire(ByteBudget(maximum_total_bytes), repository_root)


@app.command(CliCommandName.DOCTOR)
def doctor_entry(repository_root: Path = _REPOSITORY_ROOT_OPTION) -> None:
    workflow.run_doctor(repository_root)


@app.command(CliCommandName.PREPROCESS)
def preprocess_entry(
    dataset: Optional[DatasetSelector] = OptionalDatasetArgument,
    overwrite: bool = OverwriteOption,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    workflow.run_preprocess(dataset, overwrite, repository_root)


@app.command(CliCommandName.PLAN)
def plan_entry(repository_root: Path = _REPOSITORY_ROOT_OPTION) -> None:
    workflow.run_plan(repository_root)


@app.command(CliCommandName.SMOKE)
def smoke_entry(
    overwrite: bool = OverwriteOption,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    workflow.run_smoke(overwrite, repository_root)


@app.command(CliCommandName.RUN)
def run_entry(
    workflow_name: ExecutableWorkflowName,
    overwrite: bool = OverwriteOption,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    workflow.run_experiment(workflow_name, overwrite, repository_root)


@app.command(CliCommandName.STATUS)
def status_entry(
    workflow_name: Optional[ExecutableWorkflowName] = OptionalWorkflowArgument,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    workflow.run_status(workflow_name, repository_root)


@app.command(CliCommandName.REPORT)
def report_entry(
    workflow_name: Optional[ExecutableWorkflowName] = OptionalWorkflowArgument,
    overwrite: bool = OverwriteOption,
    repository_root: Path = _REPOSITORY_ROOT_OPTION,
) -> None:
    workflow.run_report(workflow_name, overwrite, repository_root)


def main() -> None:
    app()
