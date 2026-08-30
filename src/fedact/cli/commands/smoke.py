from __future__ import annotations

from pathlib import Path

import typer

from fedact.app import Application, discover_repository_root
from fedact.config.models import FederationGeometry
from fedact.datasets.synthetic.generator import (
    SYNTHETIC_DIMENSION,
    build_nuisance_spaces,
    draw_shared_transition,
    nuisance_dimension,
    seeded_generator,
)
from fedact.datasets.synthetic.validation import run_smoke_validation
from fedact.domain.types import OverwriteRequested


def run(overwrite: OverwriteRequested, repository_root: Path) -> None:
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
    transition = draw_shared_transition(rng, synth)
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
        typer.echo("smoke validation failed", err=True)
        raise typer.Exit(code=1)
    typer.echo("smoke validation passed")
