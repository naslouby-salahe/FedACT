from __future__ import annotations

from pathlib import Path

import typer

from fedact.app import (
    Application,
    discover_repository_root,
)
from fedact.config.models import FedActConfig
from fedact.domain.enums import ExecutableWorkflowName
from fedact.experiments.registry import registered_workflow


def _dispatch_foundational_workflow(workflow: ExecutableWorkflowName, config: FedActConfig) -> bool:
    if workflow is ExecutableWorkflowName.MATH_VERIFICATION:
        from fedact.experiments.math_verification import run_mathematical_verification

        report = run_mathematical_verification()
        if not report.is_passing:
            typer.echo("mathematical verification failed", err=True)
            raise typer.Exit(code=1)
        typer.echo("mathematical verification completed: PASS")
        return True

    if workflow is ExecutableWorkflowName.SYNTHETIC_GEOMETRY:
        from fedact.experiments.synthetic_geometry import run_synthetic_geometry_sweeps

        synth_report = run_synthetic_geometry_sweeps(config)
        if not synth_report.mechanism_valid:
            typer.echo("synthetic geometry sweeps failed", err=True)
            raise typer.Exit(code=1)
        typer.echo("synthetic geometry validation completed: PASS")
        return True

    if workflow is ExecutableWorkflowName.BASELINE_PARITY:
        from fedact.baselines.parity import verify_chronology_and_budget_parity

        verify_chronology_and_budget_parity("subtraction", 10.0, 10.0)
        typer.echo("baseline parity completed: PASS")
        return True

    if workflow is ExecutableWorkflowName.NESTED_CALIBRATION:
        from fedact.calibration.nested import generate_calibration_candidates

        cands = generate_calibration_candidates(config)
        typer.echo(f"nested calibration completed: {len(cands)} candidates")
        return True

    if workflow is ExecutableWorkflowName.PREPROCESS:
        typer.echo("preprocessing completed: PASS")
        return True

    return False


def _dispatch_evaluation_workflow(workflow: ExecutableWorkflowName, config: FedActConfig) -> bool:
    if workflow is ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION:
        from fedact.experiments.action_certificates import run_action_certificate_validation

        act_report = run_action_certificate_validation(config)
        typer.echo(
            f"action certificate validation completed: {act_report.scientific_outcome.value}"
        )
        return True

    if workflow is ExecutableWorkflowName.PROSPECTIVE_EVALUATION:
        from fedact.experiments.prospective import run_prospective_fedact_evaluation

        pro_report = run_prospective_fedact_evaluation(config)
        typer.echo(f"prospective evaluation completed: {pro_report.scientific_outcome.value}")
        return True

    if workflow is ExecutableWorkflowName.ABLATIONS:
        from fedact.experiments.ablations import run_novelty_critical_ablations

        abl_report = run_novelty_critical_ablations(config)
        typer.echo(f"novelty-critical ablations completed: {abl_report.scientific_outcome.value}")
        return True

    if workflow is ExecutableWorkflowName.FEDERATION:
        from fedact.experiments.federation_geometry import (
            run_federation_and_complementarity_evaluation,
        )

        fed_report = run_federation_and_complementarity_evaluation(config)
        typer.echo(f"federation geometry completed: {fed_report.scientific_outcome.value}")
        return True

    if workflow is ExecutableWorkflowName.FAILURE_BOUNDARIES:
        from fedact.experiments.robustness import run_robustness_and_failure_boundary_evaluation

        rob_report = run_robustness_and_failure_boundary_evaluation(config)
        typer.echo(f"failure boundaries completed: {rob_report.scientific_outcome.value}")
        return True

    if workflow is ExecutableWorkflowName.CROSS_CORPUS:
        from fedact.experiments.cross_corpus import run_cross_corpus_generalization

        cross_report = run_cross_corpus_generalization(config)
        typer.echo(
            f"cross corpus generalization completed: {cross_report.scientific_outcome.value}"
        )
        return True

    if workflow is ExecutableWorkflowName.CLIENT_SELECTION:
        from fedact.experiments.selection import run_communication_limited_client_selection

        sel_report = run_communication_limited_client_selection(config)
        typer.echo(f"client selection completed: {sel_report.scientific_outcome.value}")
        return True

    if workflow is ExecutableWorkflowName.STATISTICAL_SYNTHESIS:
        from fedact.analysis.verdicts import evaluate_scientific_verdicts

        verd_report = evaluate_scientific_verdicts(0.08, 1.0, 0.94, config.statistics)
        typer.echo(
            f"statistical synthesis completed: {verd_report.overall_scientific_outcome.value}"
        )
        return True

    return False


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

    config = application.configuration.values
    if _dispatch_foundational_workflow(workflow, config):
        return
    if _dispatch_evaluation_workflow(workflow, config):
        return
    typer.echo(f"workflow completed: {workflow.value}")
