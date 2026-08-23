from __future__ import annotations

import numpy as np

from fedact.config.loading import LoadedConfiguration
from fedact.config.models import FederationGeometry
from fedact.datasets.synthetic.generator import (
    SYNTHETIC_DIMENSION,
    build_nuisance_spaces,
    draw_shared_transition,
    nuisance_dimension,
)
from fedact.datasets.synthetic.validation import run_smoke_validation
from fedact.experiments.synthetic_geometry import run_synthetic_geometry_sweeps


def test_synthetic_end_to_end_pipeline(
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
    smoke_rep = run_smoke_validation(
        spaces=spaces,
        transition=transition,
        requested_nuisance_dimension=nuis_dim,
        common_intersection=synth.defaults.common_intersection_dimension,
        rank_tolerance=config.numerical.rank_clip_epsilon_relative,
        orthonormality_tolerance=config.numerical.projection_tie_tolerance,
        seed_pair=seed_pair,
    )
    assert smoke_rep.is_passing

    sweep_rep = run_synthetic_geometry_sweeps(config)
    assert sweep_rep.mechanism_valid
