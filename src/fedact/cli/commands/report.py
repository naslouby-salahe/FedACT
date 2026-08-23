from __future__ import annotations

from pathlib import Path

import typer

from fedact.app import (
    PRODUCER_NOT_REGISTERED_EXIT_CODE,
    Application,
    discover_repository_root,
)
from fedact.domain.enums import ExecutableWorkflowName


def run(workflow: ExecutableWorkflowName | None, overwrite: bool, repository_root: Path) -> None:
    Application.from_repository_root(discover_repository_root(repository_root))
    scope = workflow.value if workflow is not None else "all eligible completed workflows"
    typer.echo(f"report scope: {scope}")
    if overwrite:
        typer.echo("overwrite: scoped to reporting artifacts")
    typer.echo(
        "reporting producers are registered by the manuscript-evidence milestone",
        err=True,
    )
    raise typer.Exit(code=PRODUCER_NOT_REGISTERED_EXIT_CODE)
