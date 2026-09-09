from __future__ import annotations

import random
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import numpy as np
import typer

from fedact.analysis.reporting import export_verified_project_evidence
from fedact.artifacts import (
    ArtifactDependencyIndex,
    ArtifactIdentity,
    DependencyFingerprint,
    WorkflowResultRecord,
    WorkspaceLayout,
    read_workflow_result,
    write_workflow_result,
)
from fedact.config.loading import LoadedConfiguration, load_production_configuration
from fedact.data.ember2024 import run_empty_ember_transform_audit
from fedact.data.lamda import (
    lamda_client_semantics,
    lamda_schema_manifest,
    load_lamda_records,
    standardize_features,
    validate_lamda_dataset,
    year_month_to_calendar_month,
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
from fedact.domain.records import BoundaryFingerprints
from fedact.domain.types import (
    ActionDecision,
    ArtifactBoundary,
    DataAvailabilityFlag,
    DatasetSelector,
    DiagnosisMessage,
    ExecutableWorkflowName,
    ExecutionReason,
    ExperimentName,
    FederationGeometry,
    OptionalFlag,
    OverwriteRequested,
    RunnableWorkflowName,
    ScientificOutcome,
    SeedValue,
    SplitCutoffIdentity,
)
from fedact.experiments.registry import (
    PREPROCESS_OWNED_BOUNDARIES,
    PREPROCESS_STAGE_FLOW,
    ReuseDecision,
    SharedProducer,
    is_preprocess_triggerable,
    ownership_for,
    registered_workflow,
)
from fedact.experiments.generalization import (
    run_cross_corpus_generalization,
    run_prospective_fedact_evaluation,
)
from fedact.experiments.robustness import (
    run_communication_limited_client_selection,
    run_federation_geometry_evaluation,
    run_novelty_critical_ablations,
)
from fedact.experiments.synthesis import run_statistical_synthesis
from fedact.experiments.validation import (
    run_action_certificate_validation,
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
    FAILED = "FAILED"
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


class ArtifactExecutionState(StrEnum):
    STAGING = "STAGING"
    COMPLETE = "COMPLETE"
    STALE = "STALE"
    INVALID = "INVALID"

def apply_python_seed(seed: SeedValue) -> None:
    random.seed(seed)


def create_numpy_generator(seed: SeedValue) -> np.random.Generator:
    seed_sequence = np.random.SeedSequence(seed)
    return np.random.default_rng(seed_sequence)

WORKFLOW_DEPENDENCIES: dict[ExecutableWorkflowName, tuple[ExecutableWorkflowName, ...]] = {
    ExecutableWorkflowName.PREPROCESS: (),
    ExecutableWorkflowName.SMOKE: (),
    ExecutableWorkflowName.MATH_VERIFICATION: (),
    ExecutableWorkflowName.SYNTHETIC_GEOMETRY: (
        ExecutableWorkflowName.MATH_VERIFICATION,
        ExecutableWorkflowName.SMOKE,
    ),
    ExecutableWorkflowName.BASELINE_PARITY: (ExecutableWorkflowName.PREPROCESS,),
    ExecutableWorkflowName.NESTED_CALIBRATION: (
        ExecutableWorkflowName.PREPROCESS,
        ExecutableWorkflowName.BASELINE_PARITY,
    ),
    ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION: (
        ExecutableWorkflowName.PREPROCESS,
        ExecutableWorkflowName.BASELINE_PARITY,
        ExecutableWorkflowName.NESTED_CALIBRATION,
    ),
    ExecutableWorkflowName.PROSPECTIVE_EVALUATION: (
        ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION,
    ),
    ExecutableWorkflowName.ABLATIONS: (ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
    ExecutableWorkflowName.FEDERATION: (ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
    ExecutableWorkflowName.FAILURE_BOUNDARIES: (ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
    ExecutableWorkflowName.CROSS_CORPUS: (
        ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
        ExecutableWorkflowName.FAILURE_BOUNDARIES,
        ExecutableWorkflowName.PREPROCESS,
    ),
    ExecutableWorkflowName.CLIENT_SELECTION: (ExecutableWorkflowName.FEDERATION,),
    ExecutableWorkflowName.STATISTICAL_SYNTHESIS: (
        ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION,
        ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
        ExecutableWorkflowName.ABLATIONS,
        ExecutableWorkflowName.FEDERATION,
        ExecutableWorkflowName.FAILURE_BOUNDARIES,
        ExecutableWorkflowName.CROSS_CORPUS,
    ),
}

OPTIONAL_WORKFLOWS: frozenset[ExecutableWorkflowName] = frozenset(
    {ExecutableWorkflowName.CLIENT_SELECTION}
)


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
        raise KeyError(f"Workflow {workflow.value} not found in plan")


def _evaluate_dependency_blockers(
    dependencies: tuple[ExecutableWorkflowName, ...],
    outcomes: WorkflowOutcomeHistory,
) -> tuple[tuple[DiagnosisMessage, ...], tuple[ExecutableWorkflowName, ...]]:
    recorded = workflows_with_recorded_outcomes(outcomes)
    blocking: list[DiagnosisMessage] = []
    blocking_deps: list[ExecutableWorkflowName] = []
    for dependency in dependencies:
        if dependency not in recorded:
            blocking.append(f"dependency_unmet: {dependency.value}")
            blocking_deps.append(dependency)
        elif outcome_for_workflow(outcomes, dependency) is ScientificOutcome.FAIL:
            blocking.append(f"dependency_outcome_failed: {dependency.value}")
            blocking_deps.append(dependency)
    return tuple(blocking), tuple(blocking_deps)


def _build_entry_for_workflow(
    workflow: ExecutableWorkflowName,
    dependencies: tuple[ExecutableWorkflowName, ...],
    outcomes: WorkflowOutcomeHistory,
) -> WorkflowPlanEntry:
    is_optional = workflow in OPTIONAL_WORKFLOWS
    outcome = outcome_for_workflow(outcomes, workflow)

    if outcome is not None:
        status = (
            WorkflowExecutionState.COMPLETED
            if outcome != ScientificOutcome.FAIL
            else WorkflowExecutionState.FAILED
        )
        return WorkflowPlanEntry(
            workflow=workflow,
            status=status,
            blocking_reasons=(outcome.value,),
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
        _build_entry_for_workflow(workflow, dependencies, outcomes)
        for workflow, dependencies in WORKFLOW_DEPENDENCIES.items()
    ]
    return ExecutionPlan(entries=tuple(entries))

@dataclass(frozen=True)
class IndexedArtifact:
    identity: ArtifactIdentity
    boundary: ArtifactBoundary
    state: ArtifactExecutionState
    dependency_fingerprint: DependencyFingerprint
    upstream_identities: tuple[ArtifactIdentity, ...]


@dataclass(frozen=True)
class BoundaryDecision:
    boundary: ArtifactBoundary
    action: ActionDecision
    reused_identity: ArtifactIdentity | None
    reason: ExecutionReason


@dataclass(frozen=True)
class ResolutionPlan:
    decisions: tuple[BoundaryDecision, ...]
    newly_stale: tuple[ArtifactIdentity, ...]

    def recompute_boundaries(self) -> tuple[ArtifactBoundary, ...]:
        return tuple(
            decision.boundary for decision in self.decisions if decision.action == "recompute"
        )

    def reuse_identities(self) -> tuple[ArtifactIdentity, ...]:
        return tuple(
            decision.reused_identity
            for decision in self.decisions
            if decision.action == "reuse" and decision.reused_identity is not None
        )


EXECUTABLE_WORKFLOW_BOUNDARY_MAP: dict[ExecutableWorkflowName, tuple[ArtifactBoundary, ...]] = {
    ExecutableWorkflowName.PREPROCESS: (
        ArtifactBoundary.DATASET_PREPARATION,
        ArtifactBoundary.PREPROCESSING_AND_SPLITS,
    ),
    ExecutableWorkflowName.BASELINE_PARITY: (ArtifactBoundary.TRAINING_CHECKPOINTS,),
    ExecutableWorkflowName.NESTED_CALIBRATION: (ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,),
    ExecutableWorkflowName.PROSPECTIVE_EVALUATION: (ArtifactBoundary.EVALUATION,),
    ExecutableWorkflowName.STATISTICAL_SYNTHESIS: (ArtifactBoundary.ANALYSIS,),
}


def owned_boundaries_for_workflow(
    workflow: ExecutableWorkflowName,
) -> tuple[ArtifactBoundary, ...]:
    return EXECUTABLE_WORKFLOW_BOUNDARY_MAP.get(workflow, ())


def _active_candidate_for_boundary(
    boundary: ArtifactBoundary,
    indexed: tuple[IndexedArtifact, ...],
    index: ArtifactDependencyIndex,
    expected_fingerprint: DependencyFingerprint | None,
) -> IndexedArtifact | None:
    candidates = [
        artifact
        for artifact in indexed
        if artifact.boundary is boundary
        and artifact.state is ArtifactExecutionState.COMPLETE
        and (
            expected_fingerprint is None or artifact.dependency_fingerprint == expected_fingerprint
        )
        and index.is_active(artifact.identity)
        and all(index.is_active(upstream) for upstream in artifact.upstream_identities)
    ]
    if not candidates:
        return None
    return candidates[0]


def _normalize_indexed(
    indexed: tuple[IndexedArtifact, ...] | None,
    indexed_artifacts: tuple[IndexedArtifact, ...] | None,
) -> tuple[IndexedArtifact, ...]:
    if indexed is not None:
        return indexed
    if indexed_artifacts is not None:
        return indexed_artifacts
    return ()


def _normalize_index(
    index: ArtifactDependencyIndex | None,
    dependency_index: ArtifactDependencyIndex | None,
) -> ArtifactDependencyIndex:
    if index is not None:
        return index
    if dependency_index is not None:
        return dependency_index
    return ArtifactDependencyIndex()


def _deactivate_mismatches(
    actual_indexed: tuple[IndexedArtifact, ...],
    actual_index: ArtifactDependencyIndex,
    expected_fingerprints: BoundaryFingerprints,
) -> None:
    for candidate_artifact in actual_indexed:
        exp_fp = expected_fingerprints.for_boundary(candidate_artifact.boundary)
        if exp_fp is not None and candidate_artifact.dependency_fingerprint != exp_fp:
            actual_index.deactivate(candidate_artifact.identity)
            for desc in actual_index.descendants(candidate_artifact.identity):
                actual_index.deactivate(desc)


def resolve_execution_requirements(
    required_boundaries: tuple[ArtifactBoundary, ...],
    indexed: tuple[IndexedArtifact, ...] | None = None,
    index: ArtifactDependencyIndex | None = None,
    expected_fingerprints: BoundaryFingerprints | None = None,
    force_recompute_boundaries: frozenset[ArtifactBoundary] = frozenset(),
    overwrite_boundaries: frozenset[ArtifactBoundary] = frozenset(),
    indexed_artifacts: tuple[IndexedArtifact, ...] | None = None,
    dependency_index: ArtifactDependencyIndex | None = None,
) -> ResolutionPlan:
    actual_indexed = _normalize_indexed(indexed, indexed_artifacts)
    actual_index = _normalize_index(index, dependency_index)
    actual_expected_fingerprints = expected_fingerprints or BoundaryFingerprints()

    decisions: list[BoundaryDecision] = []
    newly_stale: list[ArtifactIdentity] = []
    recompute_cascading = False
    forces = force_recompute_boundaries | overwrite_boundaries

    if actual_expected_fingerprints:
        _deactivate_mismatches(actual_indexed, actual_index, actual_expected_fingerprints)

    for boundary in required_boundaries:
        expected_fp = actual_expected_fingerprints.for_boundary(boundary)
        candidate = _active_candidate_for_boundary(
            boundary, actual_indexed, actual_index, expected_fp
        )
        must_recompute = boundary in forces or recompute_cascading or candidate is None
        if must_recompute:
            recompute_cascading = True
            if candidate is not None and boundary in forces:
                newly_stale.append(candidate.identity)
            reason = "forced" if boundary in forces else "upstream_modified_or_missing"
            decisions.append(
                BoundaryDecision(
                    boundary=boundary,
                    action="recompute",
                    reused_identity=None,
                    reason=reason,
                )
            )
        else:
            assert candidate is not None
            decisions.append(
                BoundaryDecision(
                    boundary=boundary,
                    action="reuse",
                    reused_identity=candidate.identity,
                    reason="fingerprint_matched_active",
                )
            )
    return ResolutionPlan(decisions=tuple(decisions), newly_stale=tuple(newly_stale))

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
        return self.workspace_layout().result_experiment_directory(ExperimentName(workflow.value))

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
    typer.echo(f"preprocess scope: {' '.join(item.value for item in scope)}")
    if overwrite:
        decision = ReuseDecision.OVERWRITE
        typer.echo(f"overwrite: scoped to preprocess-owned artifacts ({decision.value})")

    for stage in PREPROCESS_STAGE_FLOW:
        typer.echo(f"stage[{stage.stage_order}]: {stage.name}")

    for selected in scope:
        source = dataset_source_chronology(selected)
        eligible = enumerate_rolling_cutoffs(
            source,
            config.temporal.historical_training_window_months,
            config.temporal.primary_confirmatory_horizon_months,
            config.temporal.cutoff_step_months,
        )
        primary = [cutoff for cutoff in eligible if cutoff.primary_confirmatory]
        typer.echo(f"{selected.value}: cutoffs={len(eligible)} primary_confirmatory={len(primary)}")
        first_identity = eligible[0].cutoff_identity
        last_identity = eligible[-1].cutoff_identity
        chronology = audit_chronology(
            dataset=selected,
            cutoff_identity=last_identity,
            source=source,
            history_start_month=source.first_observed_month,
            cutoff_exclusive_end_month=calendar_month(source.last_observed_month + 1),
        )
        typer.echo(
            f"{selected.value}: chronology_audit={'PASS' if chronology.is_passing else 'FAIL'}"
        )
        typer.echo(f"{selected.value}: first_cutoff={first_identity} last_cutoff={last_identity}")

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
                    f"{selected.value}: eligibility_role={eligibility.role.value} "
                    f"observed_rows={manifest.observed_row_count}"
                )
                if eligibility.role is DatasetEligibilityRole.UNUSABLE:
                    typer.echo(
                        f"{selected.value}: WARNING dataset is unusable for the intended evidence"
                    )

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
                    cutoff_identity=SplitCutoffIdentity(f"{selected.value}-2023-11"),
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
                    f"{selected.value}: prepared_retained={len(prepared.retained)} "
                    f"exclusions={len(prepared.exclusions)} "
                    f"reasons={len(exclusion_reasons)}"
                )
                cutoff_split = construct_cutoff_split(
                    cutoff_identity=SplitCutoffIdentity(f"{selected.value}-2023-11"),
                    sample_ids=tuple(record.sample_hash for record in loaded_lamda.records),
                    training_indices=frozenset(training_indices),
                    validation_indices=frozenset(validation_indices),
                    test_indices=frozenset(test_indices),
                    operator_eligible=frozenset(),
                )
                partition_counts = cutoff_split.partition_counts()
                training_count = partition_counts.for_partition(SplitPartition.TRAINING)
                validation_count = partition_counts.for_partition(SplitPartition.VALIDATION)
                test_count = partition_counts.for_partition(SplitPartition.TEST)
                typer.echo(
                    f"{selected.value}: split training={training_count} "
                    f"validation={validation_count} test={test_count}"
                )
            else:
                typer.echo(f"{selected.value}: raw data unavailable at {baseline_directory}")
        elif selected is DatasetSelector.EMBER2024:
            run_empty_ember_transform_audit()

    fit_ownership = ownership_for(SharedProducer.REPRESENTATION_DETECTOR_FIT)
    typer.echo(f"shared_producer: {fit_ownership.producer.value} ({fit_ownership.reuse_scope})")
    typer.echo(
        "preprocess may trigger representation fit only: "
        f"{is_preprocess_triggerable(SharedProducer.REPRESENTATION_DETECTOR_FIT)}"
    )
    boundaries = " ".join(boundary.value for boundary in PREPROCESS_OWNED_BOUNDARIES)
    typer.echo(f"owned_boundaries: {boundaries}")
    write_workflow_result(
        application.result_experiment_directory(ExecutableWorkflowName.PREPROCESS),
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
        write_workflow_result(
            app_instance.result_experiment_directory(ExecutableWorkflowName.SMOKE),
            WorkflowResultRecord(
                workflow=ExecutableWorkflowName.SMOKE,
                scientific_outcome=ScientificOutcome.FAIL,
            ),
        )
        typer.echo("smoke validation failed", err=True)
        raise typer.Exit(code=1)
    write_workflow_result(
        app_instance.result_experiment_directory(ExecutableWorkflowName.SMOKE),
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

def run_report(
    workflow: ExecutableWorkflowName | None,
    overwrite: OverwriteRequested,
    repository_root: Path,
) -> None:
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

    export_verified_project_evidence(prospective, overall_outcome, root / "results")
    typer.echo(f"manuscript evidence reporting completed: {overall_outcome.value}")

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


def run_experiment(
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
