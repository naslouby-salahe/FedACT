from __future__ import annotations

import numpy as np
from typer.testing import CliRunner

from fedact.cli.main import app
from fedact.config.loading import LoadedConfiguration
from fedact.config.models import FederationGeometry
from fedact.datasets.synthetic.generator import (
    SYNTHETIC_DIMENSION,
    build_nuisance_spaces,
    draw_shared_transition,
    nuisance_dimension,
)
from fedact.datasets.synthetic.validation import run_smoke_validation

runner = CliRunner()


def test_synthetic_generator_smoke_validation(
    production_configuration: LoadedConfiguration,
) -> None:
    config = production_configuration.values
    rng = np.random.default_rng(config.seeds.synthetic_generation[0])
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
    assert report.is_passing


def test_cli_smoke_command() -> None:
    result = runner.invoke(app, ["smoke"])
    assert result.exit_code == 0
    assert "smoke validation passed" in result.output
