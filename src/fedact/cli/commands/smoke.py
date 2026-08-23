from __future__ import annotations

from pathlib import Path

import typer

from fedact.app import (
    PRODUCER_NOT_REGISTERED_EXIT_CODE,
    Application,
    discover_repository_root,
)


def run(overwrite: bool, repository_root: Path) -> None:
    Application.from_repository_root(discover_repository_root(repository_root))
    typer.echo("synthetic generator smoke validation")
    if overwrite:
        typer.echo("overwrite: scoped to smoke-owned artifacts")
    typer.echo(
        "smoke producers are registered by the synthetic validation milestone",
        err=True,
    )
    raise typer.Exit(code=PRODUCER_NOT_REGISTERED_EXIT_CODE)
