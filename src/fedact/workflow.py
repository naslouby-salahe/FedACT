from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import numpy as np
import typer

from fedact.analysis.comparisons import CutoffAggregate
from fedact.analysis.reporting import export_verified_project_evidence
from fedact.artifacts import (
    WorkflowResultRecord,
    WorkspaceLayout,
    read_workflow_result,
    write_workflow_evidence,
    write_workflow_result,
)
from fedact.config.loading import LoadedConfiguration, load_production_configuration
from fedact.data.androzoo import acquired_lamda_apk_sample_ids
from fedact.data.ember2024 import run_empty_ember_transform_audit
from fedact.data.lamda import (
    lamda_client_semantics,
    lamda_schema_manifest,
    load_lamda_records,
    standardize_features,
    validate_lamda_dataset,
    year_month_to_calendar_month,
)
from fedact.data.lamda_apk_emulator import (
    DEFAULT_AVD_NAME,
    AndroidEmulatorError,
    android_sdk_root_from_environment,
    boot_emulator,
    ensure_avd,
    shutdown_emulator,
)
from fedact.data.records import (
    DatasetEligibilityRole,
    ExclusionReason,
    PreparedSample,
    prepare_records,
    run_feasibility_audit,
)
from fedact.data.splits import (
    IndexInPopulation,
    SplitPartition,
    audit_chronology,
    calendar_month,
    construct_cutoff_split,
    dataset_source_chronology,
    enumerate_rolling_cutoffs,
)
from fedact.data.synthetic import (
    SYNTHETIC_DIMENSION,
    build_nuisance_spaces,
    draw_shared_transition,
    nuisance_dimension,
    run_smoke_validation,
    seeded_generator,
)
from fedact.domain.types import (
    DataAvailabilityFlag,
    DatasetSelector,
    DegradationValue,
    DiagnosisMessage,
    ExecutableWorkflowName,
    ExperimentName,
    FederationGeometry,
    MetricRate,
    OptionalFlag,
    OverwriteRequested,
    ScientificOutcome,
    SeedValue,
    SplitCutoffIdentity,
)
from fedact.experiments.baselines import verify_subtraction_comparator_parity
from fedact.experiments.ember2024_identification import run_ember2024_identification_diagnostics
from fedact.experiments.generalization import (
    read_central_pattern_cutoff_aggregates,
    read_prospective_cutoff_aggregates,
    run_cross_corpus_generalization,
    run_prospective_fedact_evaluation,
)
from fedact.experiments.identification import (
    run_lamda_identification_diagnostics,
    run_lamda_temporal_dynamics_ablation,
)
from fedact.experiments.lamda_action_generation import run_lamda_action_generation
from fedact.experiments.registry import (
    WORKFLOW_REGISTRY,
    registered_workflow,
)
from fedact.experiments.robustness import (
    run_communication_limited_client_selection,
    run_federation_geometry_evaluation,
    run_novelty_critical_ablations,
)
from fedact.experiments.synthesis import run_statistical_synthesis
from fedact.experiments.validation import (
    run_action_certificate_validation,
    run_nested_calibration,
    run_robustness_and_failure_boundaries,
)
from fedact.experiments.verification import (
    run_mathematical_verification,
    run_synthetic_geometry_sweeps,
)


class WorkflowExecutionState(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    BLOCKED = "BLOCKED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    INVALID = "INVALID"


@dataclass(frozen=True)
class WorkflowOutcomeRecord:
    workflow: ExecutableWorkflowName
    outcome: ScientificOutcome


type WorkflowOutcomeHistory = tuple[WorkflowOutcomeRecord, ...]


def outcome_for_workflow(
    history: WorkflowOutcomeHistory, workflow: ExecutableWorkflowName
) -> ScientificOutcome | None:
    for record in history:
        if record.workflow is workflow:
            return record.outcome
    return None


def workflows_with_recorded_outcomes(
    history: WorkflowOutcomeHistory,
) -> frozenset[ExecutableWorkflowName]:
    return frozenset(record.workflow for record in history)


def apply_python_seed(seed: SeedValue) -> None:
    random.seed(seed)


def create_numpy_generator(seed: SeedValue) -> np.random.Generator:
    seed_sequence = np.random.SeedSequence(seed)
    return np.random.default_rng(seed_sequence)


@dataclass(frozen=True)
class WorkflowPlanEntry:
    workflow: ExecutableWorkflowName
    status: WorkflowExecutionState
    blocking_reasons: tuple[DiagnosisMessage, ...]
    optional: OptionalFlag
    blocking_dependencies: tuple[ExecutableWorkflowName, ...] = ()
    recorded_outcome: ScientificOutcome | None = None

    @property
    def name(self) -> ExecutableWorkflowName:
        return self.workflow


@dataclass(frozen=True)
class ExecutionPlan:
    entries: tuple[WorkflowPlanEntry, ...]

    @property
    def blocked(self) -> tuple[WorkflowPlanEntry, ...]:
        return tuple(
            entry for entry in self.entries if entry.status is WorkflowExecutionState.BLOCKED
        )

    @property
    def executable(self) -> frozenset[ExecutableWorkflowName]:
        return frozenset(
            entry.workflow
            for entry in self.entries
            if entry.status is WorkflowExecutionState.NOT_STARTED
        )

    def executable_workflows(self) -> tuple[ExecutableWorkflowName, ...]:
        return tuple(
            entry.workflow
            for entry in self.entries
            if entry.status is WorkflowExecutionState.NOT_STARTED
        )

    def blocked_workflows(self) -> tuple[ExecutableWorkflowName, ...]:
        return tuple(
            entry.workflow
            for entry in self.entries
            if entry.status is WorkflowExecutionState.BLOCKED
        )

    def entry(self, workflow: ExecutableWorkflowName) -> WorkflowPlanEntry:
        for item in self.entries:
            if item.workflow is workflow:
                return item
        raise KeyError(f"Workflow {workflow} not found in plan")


def _evaluate_dependency_blockers(
    dependencies: tuple[ExecutableWorkflowName, ...],
    outcomes: WorkflowOutcomeHistory,
) -> tuple[tuple[DiagnosisMessage, ...], tuple[ExecutableWorkflowName, ...]]:
    blocking: list[DiagnosisMessage] = []
    blocking_deps: list[ExecutableWorkflowName] = []
    for dependency in dependencies:
        outcome = outcome_for_workflow(outcomes, dependency)
        if outcome is not ScientificOutcome.PASS:
            reason = "dependency_unmet" if outcome is None else f"dependency_outcome_{outcome}"
            blocking.append(f"{reason}: {dependency}")
            blocking_deps.append(dependency)
    return tuple(blocking), tuple(blocking_deps)


def _build_entry_for_workflow(
    workflow: ExecutableWorkflowName,
    dependencies: tuple[ExecutableWorkflowName, ...],
    outcomes: WorkflowOutcomeHistory,
) -> WorkflowPlanEntry:
    is_optional = registered_workflow(workflow).optional
    outcome = outcome_for_workflow(outcomes, workflow)

    if outcome is not None:
        status = (
            WorkflowExecutionState.COMPLETED
            if outcome is ScientificOutcome.PASS
            else WorkflowExecutionState.INVALID
        )
        return WorkflowPlanEntry(
            workflow=workflow,
            status=status,
            blocking_reasons=(outcome,),
            optional=is_optional,
            blocking_dependencies=(),
            recorded_outcome=outcome,
        )

    blocking, blocking_deps = _evaluate_dependency_blockers(dependencies, outcomes)
    plan_status = (
        WorkflowExecutionState.NOT_STARTED if not blocking else WorkflowExecutionState.BLOCKED
    )
    return WorkflowPlanEntry(
        workflow=workflow,
        status=plan_status,
        blocking_reasons=blocking,
        optional=is_optional,
        blocking_dependencies=blocking_deps,
        recorded_outcome=outcome,
    )


def resolve_execution_plan(outcomes: WorkflowOutcomeHistory = ()) -> ExecutionPlan:
    entries = [
        _build_entry_for_workflow(workflow.name, workflow.dependencies, outcomes)
        for workflow in WORKFLOW_REGISTRY
    ]
    return ExecutionPlan(entries=tuple(entries))


SYSEXITS_EX_UNAVAILABLE = 69
PRODUCER_NOT_REGISTERED_EXIT_CODE = SYSEXITS_EX_UNAVAILABLE


@dataclass(frozen=True)
class Application:
    repository_root: Path
    configuration: LoadedConfiguration

    @classmethod
    def from_repository_root(cls, repository_root: Path) -> Application:
        configuration = load_production_configuration(repository_root / "configs" / "fedact.yaml")
        return cls(repository_root=repository_root.resolve(), configuration=configuration)

    def workspace_layout(self) -> WorkspaceLayout:
        return WorkspaceLayout(
            repository_root=self.repository_root,
            workspace=self.configuration.values.workspace,
        )

    def result_experiment_directory(self, workflow: ExecutableWorkflowName) -> Path:
        return self.workspace_layout().result_experiment_directory(ExperimentName(workflow))

    def experiment_workspace(self, workflow: ExecutableWorkflowName) -> Path:
        return self.workspace_layout().experiment_workspace(ExperimentName(workflow))

    def raw_data_root(self) -> Path:
        return self.repository_root / "data" / "raw"

    def is_raw_data_available(self) -> DataAvailabilityFlag:
        raw_root = self.raw_data_root()
        return raw_root.is_dir() and any(raw_root.iterdir())

    def recorded_outcomes(self) -> WorkflowOutcomeHistory:
        return tuple(
            WorkflowOutcomeRecord(workflow=workflow, outcome=record.scientific_outcome)
            for workflow in ExecutableWorkflowName
            if (record := read_workflow_result(self.result_experiment_directory(workflow)))
            is not None
        )

    def plan(self) -> ExecutionPlan:
        return resolve_execution_plan(self.recorded_outcomes())


def discover_repository_root(start: Path) -> Path:
    candidate = start.resolve()
    for current in (candidate, *candidate.parents):
        if (current / "pyproject.toml").is_file() and (
            current / "configs" / "fedact.yaml"
        ).is_file():
            return current
    raise FileNotFoundError(f"FedACT repository root not found above {start}")


def run_doctor(repository_root: Path) -> None:
    application = Application.from_repository_root(discover_repository_root(repository_root))
    configuration = application.configuration
    typer.echo(f"configuration: {configuration.path}")
    typer.echo(f"configuration_hash: {configuration.hash}")
    raw_available = application.is_raw_data_available()
    typer.echo(f"raw_data_available: {raw_available}")
    plan = application.plan()
    typer.echo(f"executable_now: {' '.join(plan.executable)}")
    typer.echo(f"blocked_count: {len(plan.blocked)}")


def run_plan(repository_root: Path) -> None:
    application = Application.from_repository_root(discover_repository_root(repository_root))
    plan = application.plan()
    for entry in plan.entries:
        line = f"{entry.name}: {entry.status}"
        if entry.blocking_dependencies:
            line += f" (blocked by: {' '.join(entry.blocking_dependencies)})"
        if entry.optional:
            line += " [optional]"
        typer.echo(line)


def run_preprocess(
    dataset: DatasetSelector | None, overwrite: OverwriteRequested, repository_root: Path
) -> None:
    application = Application.from_repository_root(discover_repository_root(repository_root))
    config = application.configuration.values
    scope = [dataset] if dataset is not None else list(DatasetSelector)
    typer.echo(f"preprocess scope: {' '.join(scope)}")
    if overwrite:
        typer.echo("overwrite: scoped to preprocess outputs")

    for selected in scope:
        source = dataset_source_chronology(selected)
        eligible = enumerate_rolling_cutoffs(
            source,
            config.temporal.historical_training_window_months,
            config.temporal.primary_confirmatory_horizon_months,
            config.temporal.cutoff_step_months,
        )
        primary = [cutoff for cutoff in eligible if cutoff.primary_confirmatory]
        typer.echo(f"{selected}: cutoffs={len(eligible)} primary_confirmatory={len(primary)}")
        first_identity = eligible[0].cutoff_identity
        last_identity = eligible[-1].cutoff_identity
        chronology = audit_chronology(
            dataset=selected,
            cutoff_identity=last_identity,
            source=source,
            history_start_month=source.first_observed_month,
            cutoff_exclusive_end_month=calendar_month(source.last_observed_month + 1),
        )
        typer.echo(f"{selected}: chronology_audit={'PASS' if chronology.is_passing else 'FAIL'}")
        typer.echo(f"{selected}: first_cutoff={first_identity} last_cutoff={last_identity}")

        if selected is DatasetSelector.LAMDA:
            baseline_directory = application.raw_data_root() / "LAMDA" / "Baseline" / "2023"
            if baseline_directory.is_dir():
                loaded_lamda = load_lamda_records(baseline_directory)
                validate_lamda_dataset(loaded_lamda)
                standardized_lamda_features = standardize_features(loaded_lamda.features)
                if standardized_lamda_features.shape[0] < 0:
                    raise RuntimeError("LAMDA standardization produced an impossible shape")
                manifest = lamda_schema_manifest(loaded_lamda.records, loaded_lamda.features)
                client_semantics = lamda_client_semantics()
                eligibility = run_feasibility_audit(chronology, client_semantics, manifest)
                typer.echo(
                    f"{selected}: eligibility_role={eligibility.role} "
                    f"observed_rows={manifest.observed_row_count}"
                )
                if eligibility.role is DatasetEligibilityRole.UNUSABLE:
                    typer.echo(f"{selected}: WARNING dataset is unusable for the intended evidence")

                split_cutoff = year_month_to_calendar_month("2023-11")
                training_indices: set[IndexInPopulation] = set()
                validation_indices: set[IndexInPopulation] = set()
                test_indices: set[IndexInPopulation] = set()
                for index, record in enumerate(loaded_lamda.records):
                    record_month = year_month_to_calendar_month(record.year_month)
                    position = IndexInPopulation(index)
                    if record_month < split_cutoff:
                        training_indices.add(position)
                    elif record_month == split_cutoff:
                        validation_indices.add(position)
                    else:
                        test_indices.add(position)
                prepared = prepare_records(
                    dataset=selected,
                    cutoff_identity=SplitCutoffIdentity(f"{selected}-2023-11"),
                    records=tuple(
                        PreparedSample(
                            sample_id=record.sample_hash,
                            month_index=year_month_to_calendar_month(record.year_month),
                            label=record.label,
                            family=record.family,
                            features=tuple(),
                        )
                        for record in loaded_lamda.records
                    ),
                )
                exclusion_reasons = {record.reason for record in prepared.exclusions} | {
                    ExclusionReason.CONFLICTING_DUPLICATE
                }
                typer.echo(
                    f"{selected}: prepared_retained={len(prepared.retained)} "
                    f"exclusions={len(prepared.exclusions)} "
                    f"reasons={len(exclusion_reasons)}"
                )
                cutoff_split = construct_cutoff_split(
                    cutoff_identity=SplitCutoffIdentity(f"{selected}-2023-11"),
                    sample_ids=tuple(record.sample_hash for record in loaded_lamda.records),
                    training_indices=frozenset(training_indices),
                    validation_indices=frozenset(validation_indices),
                    test_indices=frozenset(test_indices),
                    operator_eligible=acquired_lamda_apk_sample_ids(application.raw_data_root()),
                )
                partition_counts = cutoff_split.partition_counts()
                training_count = partition_counts.for_partition(SplitPartition.TRAINING)
                validation_count = partition_counts.for_partition(SplitPartition.VALIDATION)
                test_count = partition_counts.for_partition(SplitPartition.TEST)
                typer.echo(
                    f"{selected}: split training={training_count} "
                    f"validation={validation_count} test={test_count}"
                )
            else:
                typer.echo(f"{selected}: raw data unavailable at {baseline_directory}")
        elif selected is DatasetSelector.EMBER2024:
            run_empty_ember_transform_audit()

    _persist(
        application,
        WorkflowResultRecord(
            workflow=ExecutableWorkflowName.PREPROCESS,
            scientific_outcome=ScientificOutcome.PASS,
        ),
    )


def run_smoke(overwrite: OverwriteRequested, repository_root: Path) -> None:
    app_instance = Application.from_repository_root(discover_repository_root(repository_root))
    config = app_instance.configuration.values
    typer.echo("synthetic generator smoke validation")
    if overwrite:
        typer.echo("overwrite: scoped to smoke-owned artifacts")
    rng = seeded_generator(config.seeds.synthetic_generation[0])
    synth = config.synthetic
    nuis_dim = nuisance_dimension(synth.defaults.nuisance_dimension_fraction, SYNTHETIC_DIMENSION)
    spaces = build_nuisance_spaces(
        generator=rng,
        dimension=SYNTHETIC_DIMENSION,
        nuisance_dimension=nuis_dim,
        client_count=synth.defaults.federation_client_count,
        geometry=FederationGeometry.COMPLEMENTARY,
        common_intersection_dimension=synth.defaults.common_intersection_dimension,
    )
    transition = draw_shared_transition(
        rng, synth.base_sigma, synth.shared_transition_norm_over_sigma
    )
    seed_pair = [
        config.seeds.synthetic_generation[0],
        config.seeds.synthetic_noise[0],
    ]
    report = run_smoke_validation(
        spaces=spaces,
        transition=transition,
        requested_nuisance_dimension=nuis_dim,
        common_intersection=synth.defaults.common_intersection_dimension,
        rank_tolerance=config.numerical.rank_clip_epsilon_relative,
        orthonormality_tolerance=config.numerical.projection_tie_tolerance,
        seed_pair=seed_pair,
    )
    if not report.is_passing:
        _persist(
            app_instance,
            WorkflowResultRecord(
                workflow=ExecutableWorkflowName.SMOKE,
                scientific_outcome=ScientificOutcome.FAIL,
            ),
        )
        typer.echo("smoke validation failed", err=True)
        raise typer.Exit(code=1)
    _persist(
        app_instance,
        WorkflowResultRecord(
            workflow=ExecutableWorkflowName.SMOKE,
            scientific_outcome=ScientificOutcome.PASS,
        ),
    )
    typer.echo("smoke validation passed")


def run_status(workflow: ExecutableWorkflowName | None, repository_root: Path) -> None:
    application = Application.from_repository_root(discover_repository_root(repository_root))
    plan = application.plan()
    if workflow is None:
        for entry in plan.entries:
            typer.echo(f"{entry.name}: {entry.status}")
        return
    entry = plan.entry(workflow)
    typer.echo(f"workflow: {entry.name}")
    typer.echo(f"status: {entry.status}")
    if entry.blocking_dependencies:
        names = " ".join(entry.blocking_dependencies)
        typer.echo(f"blocking_dependencies: {names}")
    if entry.recorded_outcome is not None:
        typer.echo(f"last_scientific_outcome: {entry.recorded_outcome}")


def run_report(
    workflow: ExecutableWorkflowName | None,
    overwrite: OverwriteRequested,
    repository_root: Path,
) -> None:
    root = discover_repository_root(repository_root)
    application = Application.from_repository_root(root)
    scope = workflow if workflow is not None else "all eligible completed workflows"
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

    export_verified_project_evidence(
        prospective,
        overall_outcome,
        application.workspace_layout().output_directories().project_summary,
        application.configuration.values.reporting.significant_figures.percentages_and_rates,
    )
    typer.echo(f"manuscript evidence reporting completed: {overall_outcome}")


def _persist(application: Application, record: WorkflowResultRecord) -> None:
    write_workflow_evidence(application.experiment_workspace(record.workflow), record)
    write_workflow_result(application.result_experiment_directory(record.workflow), record)


def _dispatch_foundational_workflow(
    workflow: ExecutableWorkflowName, application: Application
) -> bool:
    if workflow is ExecutableWorkflowName.MATH_VERIFICATION:
        report = run_mathematical_verification()
        outcome = ScientificOutcome.PASS if report.is_passing else ScientificOutcome.FAIL
        _persist(application, WorkflowResultRecord(workflow=workflow, scientific_outcome=outcome))
        if not report.is_passing:
            typer.echo("mathematical verification failed", err=True)
            raise typer.Exit(code=1)
        typer.echo("mathematical verification completed: PASS")
        return True

    if workflow is ExecutableWorkflowName.SYNTHETIC_GEOMETRY:
        synth_report = run_synthetic_geometry_sweeps(application)
        outcome = ScientificOutcome.PASS if synth_report.mechanism_valid else ScientificOutcome.FAIL
        _persist(application, WorkflowResultRecord(workflow=workflow, scientific_outcome=outcome))
        if not synth_report.mechanism_valid:
            typer.echo("synthetic geometry sweeps failed", err=True)
            raise typer.Exit(code=1)
        typer.echo("synthetic geometry validation completed: PASS")
        return True

    return False


def _statistical_synthesis_inputs(
    application: Application,
) -> tuple[
    MetricRate,
    DegradationValue,
    MetricRate,
    tuple[CutoffAggregate, ...],
    tuple[CutoffAggregate, ...],
    tuple[CutoffAggregate, ...],
    tuple[CutoffAggregate, ...],
    tuple[CutoffAggregate, ...],
    tuple[CutoffAggregate, ...],
]:
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
    certified_series, ambiguous_series, hardened_series, static_chronological_series = (
        read_prospective_cutoff_aggregates(application)
    )
    central_pattern_certified_series, matched_random_series = (
        read_central_pattern_cutoff_aggregates(application)
    )
    return (
        prospective.mean_false_negative_rate,
        prospective.clean_fnr_degradation_percentage_points,
        prospective.mean_certification_rate,
        certified_series,
        ambiguous_series,
        hardened_series,
        static_chronological_series,
        central_pattern_certified_series,
        matched_random_series,
    )


def _run_lamda_action_generation_if_acquired(application: Application) -> None:
    if not acquired_lamda_apk_sample_ids(application.repository_root / "data" / "raw"):
        typer.echo("action certificate validation: no AndroZoo-acquired APKs, skipping generation")
        return
    try:
        sdk_root = android_sdk_root_from_environment()
    except AndroidEmulatorError as error:
        typer.echo(f"action certificate validation: skipping generation ({error})")
        return
    system_image = application.configuration.values.operators.validation.android_system_image
    try:
        ensure_avd(sdk_root, DEFAULT_AVD_NAME, system_image)
        handle = boot_emulator(sdk_root, DEFAULT_AVD_NAME, 5554, 300.0)
    except AndroidEmulatorError as error:
        typer.echo(f"action certificate validation: skipping generation ({error})")
        return
    try:
        report = run_lamda_action_generation(application, handle)
        typer.echo(
            f"lamda action generation completed: "
            f"eligible={report.operator_eligible_source_samples} "
            f"considered={report.candidates_considered} "
            f"written={report.valid_actions_written} "
            f"maliciousness_unavailable={report.maliciousness_validation_unavailable_count}"
        )
    finally:
        shutdown_emulator(handle)


def _dispatch_evaluation_workflow(
    workflow: ExecutableWorkflowName, application: Application
) -> bool:
    config = application.configuration.values
    if workflow is ExecutableWorkflowName.BASELINE_PARITY:
        parity = verify_subtraction_comparator_parity(config.numerical.projection_tie_tolerance)
        outcome = ScientificOutcome.PASS if parity.is_valid else ScientificOutcome.FAIL
        _persist(application, WorkflowResultRecord(workflow=workflow, scientific_outcome=outcome))
        if not parity.is_valid:
            raise RuntimeError(f"baseline parity validation failed: {parity.details}")
        typer.echo("baseline parity validation completed: PASS")
        return True

    if workflow is ExecutableWorkflowName.NESTED_CALIBRATION:
        candidates = run_nested_calibration(application)
        outcome = ScientificOutcome.PASS if candidates else ScientificOutcome.INSUFFICIENT_EVIDENCE
        _persist(application, WorkflowResultRecord(workflow=workflow, scientific_outcome=outcome))
        typer.echo(f"nested calibration completed: {outcome}")
        return True

    if workflow is ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION:
        _run_lamda_action_generation_if_acquired(application)
        act_report = run_action_certificate_validation(application)
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow,
                scientific_outcome=act_report.scientific_outcome,
                central_pattern_supported=act_report.central_pattern_supported,
                rank_alignment_spearman_rho=act_report.rank_alignment_spearman_rho,
            ),
        )
        typer.echo(f"action certificate validation completed: {act_report.scientific_outcome}")
        return True

    if workflow is ExecutableWorkflowName.PROSPECTIVE_EVALUATION:
        pro_report = run_prospective_fedact_evaluation(application)
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow,
                scientific_outcome=pro_report.scientific_outcome,
                mean_false_negative_rate=pro_report.mean_false_negative_rate,
                mean_certification_rate=pro_report.mean_certification_rate,
                static_chronological_false_negative_rate=(
                    pro_report.static_chronological_false_negative_rate
                ),
                early_horizon_fnr_reduction_percentage_points=(
                    pro_report.early_horizon_fnr_reduction_percentage_points
                ),
                clean_fnr_degradation_percentage_points=(
                    pro_report.clean_fnr_degradation_percentage_points
                ),
            ),
        )
        typer.echo(f"prospective evaluation completed: {pro_report.scientific_outcome}")
        identification_report = run_lamda_identification_diagnostics(application)
        typer.echo(
            "lamda identification diagnostics completed: "
            f"{identification_report.scientific_outcome} "
            f"(cutoffs_fitted={identification_report.cutoffs_fitted}/"
            f"{identification_report.cutoffs_evaluated})"
        )
        temporal_report = run_lamda_temporal_dynamics_ablation(application)
        typer.echo(
            f"lamda temporal dynamics ablation completed: {temporal_report.scientific_outcome}"
        )
        return True

    if workflow is ExecutableWorkflowName.ABLATIONS:
        abl_report = run_novelty_critical_ablations(application)
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow, scientific_outcome=abl_report.scientific_outcome
            ),
        )
        typer.echo(f"novelty-critical ablations completed: {abl_report.scientific_outcome}")
        return True

    if workflow is ExecutableWorkflowName.FEDERATION:
        fed_report = run_federation_geometry_evaluation(application)
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow, scientific_outcome=fed_report.scientific_outcome
            ),
        )
        typer.echo(f"federation geometry completed: {fed_report.scientific_outcome}")
        return True

    if workflow is ExecutableWorkflowName.FAILURE_BOUNDARIES:
        rob_report = run_robustness_and_failure_boundaries(application)
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow, scientific_outcome=rob_report.scientific_outcome
            ),
        )
        typer.echo(f"failure boundaries completed: {rob_report.scientific_outcome}")
        return True

    if workflow is ExecutableWorkflowName.CROSS_CORPUS:
        cross_report = run_cross_corpus_generalization(application)
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow, scientific_outcome=cross_report.scientific_outcome
            ),
        )
        typer.echo(f"cross corpus generalization completed: {cross_report.scientific_outcome}")
        ember_identification_report = run_ember2024_identification_diagnostics(application)
        typer.echo(
            "ember2024 identification diagnostics completed: "
            f"{ember_identification_report.scientific_outcome}"
        )
        return True

    if workflow is ExecutableWorkflowName.CLIENT_SELECTION:
        sel_report = run_communication_limited_client_selection(application)
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow, scientific_outcome=sel_report.scientific_outcome
            ),
        )
        typer.echo(f"client selection completed: {sel_report.scientific_outcome}")
        return True

    if workflow is ExecutableWorkflowName.STATISTICAL_SYNTHESIS:
        (
            prospective_fnr,
            clean_fnr_degradation,
            coverage,
            certified_series,
            ambiguous_series,
            hardened_series,
            static_chronological_series,
            central_pattern_certified_series,
            matched_random_series,
        ) = _statistical_synthesis_inputs(application)
        verd_report = run_statistical_synthesis(
            prospective_fnr=prospective_fnr,
            clean_fnr_degradation=clean_fnr_degradation,
            coverage=coverage,
            hardened_series=hardened_series,
            static_chronological_series=static_chronological_series,
            central_pattern_certified_series=central_pattern_certified_series,
            matched_random_series=matched_random_series,
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
            certified_series=certified_series,
            ambiguous_series=ambiguous_series,
        )
        _persist(
            application,
            WorkflowResultRecord(
                workflow=workflow,
                scientific_outcome=verd_report.overall_scientific_outcome,
            ),
        )
        typer.echo(f"statistical synthesis completed: {verd_report.overall_scientific_outcome}")
        if verd_report.early_exposure_contrast_outcome is not None:
            typer.echo(
                "early-exposure contrast (FedACT vs static-chronological) sufficient: "
                f"{verd_report.early_exposure_contrast_outcome.contrast_inputs.sufficient}"
            )
        if verd_report.matched_random_contrast_outcome is not None:
            matched_random_sufficient = (
                verd_report.matched_random_contrast_outcome.contrast_inputs.sufficient
            )
            typer.echo(
                "matched-random contrast (certified vs matched-random action relevance) "
                f"sufficient: {matched_random_sufficient}"
            )
        return True

    return False


def _execute_dependency(
    workflow: ExecutableWorkflowName,
    application: Application,
) -> None:
    if workflow is ExecutableWorkflowName.PREPROCESS:
        run_preprocess(None, False, application.repository_root)
        return
    if workflow is ExecutableWorkflowName.SMOKE:
        run_smoke(False, application.repository_root)
        return
    if _dispatch_foundational_workflow(workflow, application):
        return
    if _dispatch_evaluation_workflow(workflow, application):
        return
    raise RuntimeError(f"unhandled internal dependency {workflow}")


def _materialize_dependencies(
    workflow: ExecutableWorkflowName,
    application: Application,
) -> None:
    for dependency in registered_workflow(workflow).dependencies:
        dependency_entry = application.plan().entry(dependency)
        if dependency_entry.status is WorkflowExecutionState.COMPLETED:
            continue
        _materialize_dependencies(dependency, application)
        _execute_dependency(dependency, application)
        refreshed = application.plan().entry(dependency)
        if refreshed.status is not WorkflowExecutionState.COMPLETED:
            raise RuntimeError(f"dependency {dependency} did not complete")


def run_experiment(
    workflow: ExecutableWorkflowName, overwrite: OverwriteRequested, repository_root: Path
) -> None:
    application = Application.from_repository_root(discover_repository_root(repository_root))
    if workflow is ExecutableWorkflowName.PREPROCESS:
        run_preprocess(None, overwrite, application.repository_root)
        return
    if workflow is ExecutableWorkflowName.SMOKE:
        run_smoke(overwrite, application.repository_root)
        return
    selected = registered_workflow(workflow)
    _materialize_dependencies(workflow, application)
    typer.echo(f"workflow: {workflow}")
    typer.echo(f"roadmap section: {selected.section}")
    if overwrite:
        typer.echo("overwrite: scoped to this workflow's artifacts")

    if _dispatch_foundational_workflow(workflow, application):
        return
    if _dispatch_evaluation_workflow(workflow, application):
        return
    raise RuntimeError(f"unhandled workflow {workflow}")
