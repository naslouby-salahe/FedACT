from __future__ import annotations

from pathlib import Path

import typer

from fedact.app import (
    PRODUCER_NOT_REGISTERED_EXIT_CODE,
    Application,
    discover_repository_root,
)
from fedact.domain.enums import DatasetSelector


def run(dataset: DatasetSelector | None, overwrite: bool, repository_root: Path) -> None:
    Application.from_repository_root(discover_repository_root(repository_root))
    scope = dataset.value if dataset is not None else "all datasets"
    typer.echo(f"preprocess scope: {scope}")
    if overwrite:
        typer.echo("overwrite: scoped to preprocess-owned artifacts")
    typer.echo(
        "dataset preparation producers are registered by the chronology-safe data milestone",
        err=True,
    )
    raise typer.Exit(code=PRODUCER_NOT_REGISTERED_EXIT_CODE)
