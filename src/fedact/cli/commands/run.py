from __future__ import annotations

from pathlib import Path

import typer

from fedact.app import (
    PRODUCER_NOT_REGISTERED_EXIT_CODE,
    Application,
    discover_repository_root,
)
from fedact.domain.enums import ExecutableWorkflowName
from fedact.experiments.registry import registered_workflow


def run(workflow: ExecutableWorkflowName, overwrite: bool, repository_root: Path) -> None:
    selected = registered_workflow(workflow)
    application = Application.from_repository_root(discover_repository_root(repository_root))
    entry = application.plan().entry(workflow)
    if entry.status == "blocked":
        typer.echo(
            f"workflow '{workflow.value}' is blocked by: "
            f"{' '.join(dep.value for dep in entry.blocking_dependencies)}",
            err=True,
        )
        raise typer.Exit(code=2)
    typer.echo(f"workflow: {workflow.value}")
    typer.echo(f"roadmap section: {selected.roadmap_section}")
    if overwrite:
        typer.echo("overwrite: scoped to this workflow's artifacts")

    if workflow is ExecutableWorkflowName.MATH_VERIFICATION:
        from fedact.experiments.math_verification import run_mathematical_verification

        report = run_mathematical_verification()
        if not report.is_passing:
            typer.echo("mathematical verification failed", err=True)
            raise typer.Exit(code=1)
        typer.echo("mathematical verification completed: PASS")
        return

    if workflow is ExecutableWorkflowName.SYNTHETIC_GEOMETRY:
        from fedact.experiments.synthetic_geometry import run_synthetic_geometry_sweeps

        synth_report = run_synthetic_geometry_sweeps(application.configuration.values)
        if not synth_report.mechanism_valid:
            typer.echo("synthetic geometry sweeps failed", err=True)
            raise typer.Exit(code=1)
        typer.echo("synthetic geometry validation completed: PASS")
        return

    typer.echo(
        f"no scientific producer is registered yet for '{workflow.value}'",
        err=True,
    )
    raise typer.Exit(code=PRODUCER_NOT_REGISTERED_EXIT_CODE)
