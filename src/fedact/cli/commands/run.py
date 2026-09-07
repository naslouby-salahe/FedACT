from __future__ import annotations

from pathlib import Path

import typer

from fedact.app import (
    Application,
    discover_repository_root,
)
from fedact.domain.enums import (
    ExecutableWorkflowName,
    RunnableWorkflowName,
    ScientificOutcome,
)
from fedact.domain.records import OverwriteRequested
from fedact.experiments import registered_workflow
from fedact.runtime.status import WorkflowExecutionState
from fedact.storage.results import (
    WorkflowResultRecord,
    read_workflow_result,
    write_workflow_result,
)

_RUNNABLE_TO_EXECUTABLE: dict[RunnableWorkflowName, ExecutableWorkflowName] = {
    RunnableWorkflowName.MATH_VERIFICATION: ExecutableWorkflowName.MATH_VERIFICATION,
    RunnableWorkflowName.SYNTHETIC_GEOMETRY: ExecutableWorkflowName.SYNTHETIC_GEOMETRY,
    RunnableWorkflowName.ACTION_CERTIFICATE_VALIDATION: (
        ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION
    ),
    RunnableWorkflowName.PROSPECTIVE_EVALUATION: ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
    RunnableWorkflowName.ABLATIONS: ExecutableWorkflowName.ABLATIONS,
    RunnableWorkflowName.FEDERATION: ExecutableWorkflowName.FEDERATION,
    RunnableWorkflowName.FAILURE_BOUNDARIES: ExecutableWorkflowName.FAILURE_BOUNDARIES,
    RunnableWorkflowName.CROSS_CORPUS: ExecutableWorkflowName.CROSS_CORPUS,
    RunnableWorkflowName.CLIENT_SELECTION: ExecutableWorkflowName.CLIENT_SELECTION,
    RunnableWorkflowName.STATISTICAL_SYNTHESIS: ExecutableWorkflowName.STATISTICAL_SYNTHESIS,
}


def _persist(application: Application, record: WorkflowResultRecord) -> None:
    write_workflow_result(application.result_experiment_directory(record.workflow), record)


def _dispatch_foundational_workflow(
    workflow: ExecutableWorkflowName, application: Application
) -> bool:
    if workflow is ExecutableWorkflowName.MATH_VERIFICATION:
        from fedact.experiments.math_verification import run_mathematical_verification

        report = run_mathematical_verification()
        outcome = ScientificOutcome.PASS if report.is_passing else ScientificOutcome.FAIL
        _persist(application, WorkflowResultRecord(workflow=workflow, scientific_outcome=outcome))
        if not report.is_passing:
            typer.echo("mathematical verification failed", err=True)
            raise typer.Exit(code=1)
        typer.echo("mathematical verification completed: PASS")
        return True

    if workflow is ExecutableWorkflowName.SYNTHETIC_GEOMETRY:
        from fedact.experiments.synthetic_geometry import run_synthetic_geometry_sweeps

        synth_report = run_synthetic_geometry_sweeps(application)
        outcome = ScientificOutcome.PASS if synth_report.mechanism_valid else ScientificOutcome.FAIL
        _persist(application, WorkflowResultRecord(workflow=workflow, scientific_outcome=outcome))
        if not synth_report.mechanism_valid:
            typer.echo("synthetic geometry sweeps failed", err=True)
            raise typer.Exit(code=1)
        typer.echo("synthetic geometry validation completed: PASS")
        return True

    return False


def _statistical_synthesis_inputs(application: Application) -> tuple[float, float, float]:
    prospective = read_workflow_result(
        application.result_experiment_directory(ExecutableWorkflowName.PROSPECTIVE_EVALUATION)
    )
    if (
        prospective is None
        or prospective.mean_false_negative_rate is None
        or prospective.clean_fnr_degradation_percentage_points is None
        or prospective.mean_certification_rate is None
    ):
        typer.echo(
            "statistical synthesis requires a completed prospective evaluation result", err=True
        )
        raise typer.Exit(code=2)
    return (
        prospective.mean_false_negative_rate,
        prospective.clean_fnr_degradation_percentage_points,
        prospective.mean_certification_rate,
    )


def _dispatch_evaluation_workflow(
    workflow: ExecutableWorkflowName, application: Application
) -> bool:
    config = application.configuration.values
    if workflow is ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION:
        from fedact.experiments.action_certificate_validation import (
            run_action_certificate_validation,
        )

        act_report = run_action_certificate_validation(application)
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow, scientific_outcome=act_report.scientific_outcome
            ),
        )
        typer.echo(
            f"action certificate validation completed: {act_report.scientific_outcome.value}"
        )
        return True

    if workflow is ExecutableWorkflowName.PROSPECTIVE_EVALUATION:
        from fedact.experiments.prospective_evaluation import run_prospective_fedact_evaluation

        pro_report = run_prospective_fedact_evaluation(application)
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow,
                scientific_outcome=pro_report.scientific_outcome,
                mean_false_negative_rate=pro_report.mean_false_negative_rate,
                mean_certification_rate=pro_report.mean_certification_rate,
                clean_fnr_degradation_percentage_points=(
                    pro_report.clean_fnr_degradation_percentage_points
                ),
            ),
        )
        typer.echo(f"prospective evaluation completed: {pro_report.scientific_outcome.value}")
        return True

    if workflow is ExecutableWorkflowName.ABLATIONS:
        from fedact.experiments.ablations import run_novelty_critical_ablations

        abl_report = run_novelty_critical_ablations(application)
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow, scientific_outcome=abl_report.scientific_outcome
            ),
        )
        typer.echo(f"novelty-critical ablations completed: {abl_report.scientific_outcome.value}")
        return True

    if workflow is ExecutableWorkflowName.FEDERATION:
        from fedact.experiments.federation import run_federation_geometry_evaluation

        fed_report = run_federation_geometry_evaluation(application)
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow, scientific_outcome=fed_report.scientific_outcome
            ),
        )
        typer.echo(f"federation geometry completed: {fed_report.scientific_outcome.value}")
        return True

    if workflow is ExecutableWorkflowName.FAILURE_BOUNDARIES:
        from fedact.experiments.failure_boundaries import run_robustness_and_failure_boundaries

        rob_report = run_robustness_and_failure_boundaries(application)
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow, scientific_outcome=rob_report.scientific_outcome
            ),
        )
        typer.echo(f"failure boundaries completed: {rob_report.scientific_outcome.value}")
        return True

    if workflow is ExecutableWorkflowName.CROSS_CORPUS:
        from fedact.experiments.cross_corpus import run_cross_corpus_generalization

        cross_report = run_cross_corpus_generalization(application)
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow, scientific_outcome=cross_report.scientific_outcome
            ),
        )
        typer.echo(
            f"cross corpus generalization completed: {cross_report.scientific_outcome.value}"
        )
        return True

    if workflow is ExecutableWorkflowName.CLIENT_SELECTION:
        from fedact.experiments.client_selection import run_communication_limited_client_selection

        sel_report = run_communication_limited_client_selection(application)
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow, scientific_outcome=sel_report.scientific_outcome
            ),
        )
        typer.echo(f"client selection completed: {sel_report.scientific_outcome.value}")
        return True

    if workflow is ExecutableWorkflowName.STATISTICAL_SYNTHESIS:
        from fedact.experiments.statistical_synthesis import run_statistical_synthesis

        prospective_fnr, clean_fnr_degradation, coverage = _statistical_synthesis_inputs(
            application
        )
        verd_report = run_statistical_synthesis(
            prospective_fnr=prospective_fnr,
            clean_fnr_degradation=clean_fnr_degradation,
            coverage=coverage,
            maximum_coverage_deficit=(
                config.statistics.minimum_material_effects.maximum_coverage_deficit_absolute
            ),
            maximum_clean_fnr_degradation=(
                config.hardening.weight.maximum_clean_fnr_degradation_percentage_points
            ),
            control_span_alphas=tuple(
                config.identification.control_span_violation.sensitivity_alpha
            ),
            private_contamination_alphas=tuple(
                config.identification.private_contamination.sensitivity_alpha
            ),
            radius_multipliers=tuple(
                config.identification.historical_plausibility_radius.sensitivity_multipliers
            ),
            alignment_percentiles=tuple(
                config.certification.alignment_threshold.percentile_candidates
            ),
            ambiguity_percentiles=tuple(config.certification.ambiguity_width.percentile_candidates),
            forecast_horizons=tuple(config.temporal.forecast_horizons_months),
            nuisance_ranks=tuple(config.identification.nuisance_rank.candidates),
            coverage_levels=tuple(config.identification.target_coverage.candidates),
            minimum_paired_cutoffs=config.statistics.minimum_paired_cutoffs,
            maximum_missing_cutoff_fraction=config.statistics.maximum_missing_cutoff_fraction,
            bootstrap_resamples=config.statistics.bootstrap.resamples,
            confidence_level=config.statistics.confidence_level,
            maximum_nonzero_pairs_for_exact=config.statistics.wilcoxon.maximum_nonzero_pairs_for_exact,
            multiplicity_q=config.statistics.multiplicity.q,
            statistics_seed=config.seeds.analysis[0],
        )
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow,
                scientific_outcome=verd_report.overall_scientific_outcome,
            ),
        )
        typer.echo(
            f"statistical synthesis completed: {verd_report.overall_scientific_outcome.value}"
        )
        return True

    return False


def run(
    workflow: RunnableWorkflowName, overwrite: OverwriteRequested, repository_root: Path
) -> None:
    executable_workflow = _RUNNABLE_TO_EXECUTABLE[workflow]
    selected = registered_workflow(executable_workflow)
    application = Application.from_repository_root(discover_repository_root(repository_root))
    entry = application.plan().entry(executable_workflow)
    if entry.status is WorkflowExecutionState.BLOCKED:
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

    if _dispatch_foundational_workflow(executable_workflow, application):
        return
    if _dispatch_evaluation_workflow(executable_workflow, application):
        return
    raise RuntimeError(f"unhandled workflow {workflow.value}")
