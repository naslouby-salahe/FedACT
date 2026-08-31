from __future__ import annotations

from pathlib import Path

import typer

from fedact.app import Application, discover_repository_root


def run(repository_root: Path) -> None:
    application = Application.from_repository_root(discover_repository_root(repository_root))
    configuration = application.configuration
    typer.echo(f"configuration: {configuration.path}")
    typer.echo(f"configuration_hash: {configuration.hash}")
    raw_available = application.is_raw_data_available()
    typer.echo(f"raw_data_available: {raw_available}")
    plan = application.plan()
    typer.echo(f"executable_now: {' '.join(plan.executable)}")
    typer.echo(f"blocked_count: {len(plan.blocked)}")
