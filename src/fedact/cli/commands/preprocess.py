from __future__ import annotations

from pathlib import Path

import typer

from fedact.app import Application, discover_repository_root
from fedact.artifacts.manifests import WorkflowResultRecord, write_workflow_result
from fedact.datasets.audits import audit_chronology, run_feasibility_audit
from fedact.datasets.chronology import (
    calendar_month,
    dataset_source_chronology,
    enumerate_rolling_cutoffs,
)
from fedact.datasets.ember2024.validation import run_empty_ember_transform_audit
from fedact.datasets.lamda.loader import load_lamda_records
from fedact.datasets.lamda.preprocessing import standardize_features
from fedact.datasets.lamda.semantics import (
    lamda_client_semantics,
    lamda_schema_manifest,
    year_month_to_calendar_month,
)
from fedact.datasets.lamda.validation import validate_lamda_dataset
from fedact.datasets.records import (
    DatasetEligibilityRole,
    ExclusionReason,
    PreparedSample,
    prepare_records,
)
from fedact.datasets.splits import IndexInPopulation, SplitPartition, construct_cutoff_split
from fedact.domain.enums import DatasetSelector, ExecutableWorkflowName, ScientificOutcome
from fedact.domain.records import OverwriteRequested, SplitCutoffIdentity
from fedact.experiments.dependencies import (
    PREPROCESS_OWNED_BOUNDARIES,
    PREPROCESS_STAGE_FLOW,
    ReuseDecision,
    SharedProducer,
    is_preprocess_triggerable,
    ownership_for,
)


def run(
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
        eligible = enumerate_rolling_cutoffs(source, config)
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
