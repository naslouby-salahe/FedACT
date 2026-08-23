from __future__ import annotations

from pathlib import Path

import typer

from fedact.app import Application, discover_repository_root
from fedact.domain.enums import ExecutableWorkflowName


def run(workflow: ExecutableWorkflowName | None, repository_root: Path) -> None:
    application = Application.from_repository_root(discover_repository_root(repository_root))
    plan = application.plan()
    if workflow is None:
        for entry in plan.entries:
            typer.echo(f"{entry.name.value}: {entry.status}")
        return
    entry = plan.entry(workflow)
    typer.echo(f"workflow: {entry.name.value}")
    typer.echo(f"status: {entry.status}")
    if entry.blocking_dependencies:
        names = " ".join(dep.value for dep in entry.blocking_dependencies)
        typer.echo(f"blocking_dependencies: {names}")
    if entry.recorded_outcome is not None:
        typer.echo(f"last_scientific_outcome: {entry.recorded_outcome.value}")
