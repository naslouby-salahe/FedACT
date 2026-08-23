from __future__ import annotations

from pathlib import Path

import typer

from fedact.app import Application, discover_repository_root


def run(repository_root: Path) -> None:
    application = Application.from_repository_root(discover_repository_root(repository_root))
    plan = application.plan()
    for entry in plan.entries:
        line = f"{entry.name}: {entry.status}"
        if entry.blocking_dependencies:
            line += f" (blocked by: {' '.join(entry.blocking_dependencies)})"
        if entry.optional:
            line += " [optional]"
        typer.echo(line)
