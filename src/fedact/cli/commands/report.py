from __future__ import annotations

from pathlib import Path

import typer

from fedact.app import Application, discover_repository_root
from fedact.artifacts.results import read_workflow_result
from fedact.domain.enums import ExecutableWorkflowName
from fedact.reporting.project_report import generate_project_report


def run(workflow: ExecutableWorkflowName | None, overwrite: bool, repository_root: Path) -> None:
    root = discover_repository_root(repository_root)
    application = Application.from_repository_root(root)
    scope = workflow.value if workflow is not None else "all eligible completed workflows"
    typer.echo(f"report scope: {scope}")
    if overwrite:
        typer.echo("overwrite: scoped to reporting artifacts")

    prospective = read_workflow_result(
        application.result_experiment_directory(ExecutableWorkflowName.PROSPECTIVE_EVALUATION)
    )
    if (
        prospective is None
        or prospective.mean_false_negative_rate is None
        or prospective.mean_certification_rate is None
        or prospective.clean_fnr_degradation_percentage_points is None
    ):
        typer.echo("report requires a completed prospective evaluation result", err=True)
        raise typer.Exit(code=1)

    synthesis = read_workflow_result(
        application.result_experiment_directory(ExecutableWorkflowName.STATISTICAL_SYNTHESIS)
    )
    overall_outcome = (
        synthesis.scientific_outcome if synthesis is not None else prospective.scientific_outcome
    )

    generate_project_report(prospective, overall_outcome, root / "results")
    typer.echo(f"manuscript evidence reporting completed: {overall_outcome.value}")
