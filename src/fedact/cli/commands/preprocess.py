from __future__ import annotations

from pathlib import Path

import typer

from fedact.app import Application, discover_repository_root
from fedact.datasets.audits import audit_chronology
from fedact.datasets.chronology import (
    LAMDA_MISSING_2015_GAP,
    SourceChronology,
    SourceGap,
    calendar_month,
    enumerate_rolling_cutoffs,
)
from fedact.domain.enums import DatasetSelector
from fedact.experiments.producers import (
    PREPROCESS_OWNED_BOUNDARIES,
    PREPROCESS_STAGE_FLOW,
    SharedProducer,
    is_preprocess_triggerable,
    ownership_for,
)

_DATASET_CHRONOLOGY: dict[DatasetSelector, tuple[int, int, tuple[SourceGap, ...]]] = {
    DatasetSelector.LAMDA: (0, 143, (LAMDA_MISSING_2015_GAP,)),
    DatasetSelector.EMBER2024: (0, 14, ()),
}


def run(dataset: DatasetSelector | None, overwrite: bool, repository_root: Path) -> None:
    application = Application.from_repository_root(discover_repository_root(repository_root))
    config = application.configuration.values
    scope = [dataset] if dataset is not None else list(DatasetSelector)
    typer.echo(f"preprocess scope: {' '.join(item.value for item in scope)}")
    if overwrite:
        typer.echo("overwrite: scoped to preprocess-owned artifacts")

    for stage in PREPROCESS_STAGE_FLOW:
        typer.echo(f"stage[{stage.stage_order}]: {stage.name}")

    for selected in scope:
        first_month, last_month, gaps = _DATASET_CHRONOLOGY[selected]
        source = SourceChronology(
            first_observed_month=calendar_month(first_month),
            last_observed_month=calendar_month(last_month),
            prohibited_gaps=gaps,
        )
        eligible = enumerate_rolling_cutoffs(source, config)
        primary = [cutoff for cutoff in eligible if cutoff.primary_confirmatory]
        typer.echo(f"{selected.value}: cutoffs={len(eligible)} primary_confirmatory={len(primary)}")
        first_identity = eligible[0].cutoff_identity
        last_identity = eligible[-1].cutoff_identity
        chronology = audit_chronology(
            dataset=selected,
            cutoff_identity=last_identity,
            source=source,
            history_start_month=calendar_month(first_month),
            cutoff_exclusive_end_month=calendar_month(last_month + 1),
        )
        typer.echo(
            f"{selected.value}: chronology_audit={'PASS' if chronology.is_passing else 'FAIL'}"
        )
        typer.echo(f"{selected.value}: first_cutoff={first_identity} last_cutoff={last_identity}")

    fit_ownership = ownership_for(SharedProducer.REPRESENTATION_DETECTOR_FIT)
    typer.echo(f"shared_producer: {fit_ownership.producer.value} ({fit_ownership.reuse_scope})")
    typer.echo(
        "preprocess may trigger representation fit only: "
        f"{is_preprocess_triggerable(SharedProducer.REPRESENTATION_DETECTOR_FIT)}"
    )
    boundaries = " ".join(boundary.value for boundary in PREPROCESS_OWNED_BOUNDARIES)
    typer.echo(f"owned_boundaries: {boundaries}")
    raise typer.Exit(code=0)
