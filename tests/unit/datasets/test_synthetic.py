from __future__ import annotations

import numpy as np
import pytest

from fedact.config.models import FederationGeometry, PrivateTransitionSparsityMode
from fedact.datasets.synthetic.generator import (
    SYNTHETIC_DIMENSION,
    build_nuisance_spaces,
    deterministic_orthonormal_basis,
    draw_private_transition,
    draw_shared_transition,
    effective_support,
    nuisance_dimension,
    paired_seed_streams,
)
from fedact.datasets.synthetic.geometry import (
    action_rotation,
    common_intersection_dimension,
    principal_angles,
    spectral_conditioning_ratio,
    true_action_score,
    verify_orthonormality,
)
from fedact.datasets.synthetic.validation import run_smoke_validation


def test_nuisance_dimension_maps_configured_fractions_exactly() -> None:
    assert [nuisance_dimension(fraction) for fraction in (0.05, 0.15, 0.30, 0.50, 0.70)] == [
        3,
        10,
        19,
        32,
        45,
    ]


def test_deterministic_basis_has_standardized_column_signs() -> None:
    generator = np.random.default_rng(7)
    basis = deterministic_orthonormal_basis(generator, SYNTHETIC_DIMENSION, 5)
    verify_orthonormality(basis, tolerance=1e-9)
    largest_rows = np.abs(basis).argmax(axis=0)
    assert all(basis[largest_rows[column], column] > 0 for column in range(basis.shape[1]))


def test_redundant_geometry_shares_one_basis_across_clients() -> None:
    generator = np.random.default_rng(1)
    spaces = build_nuisance_spaces(generator, 64, 8, 3, FederationGeometry.REDUNDANT, 2)
    first = spaces.clients[0].basis
    assert all(client.basis.shape == first.shape for client in spaces.clients)
    assert np.array_equal(first, spaces.clients[1].basis)


def test_complementary_geometry_produces_requested_intersection() -> None:
    generator = np.random.default_rng(2)
    intersection = 2
    spaces = build_nuisance_spaces(
        generator, 64, 6, 2, FederationGeometry.COMPLEMENTARY, intersection
    )
    observed = common_intersection_dimension(
        tuple(client.basis for client in spaces.clients), rank_tolerance=1e-6
    )
    assert observed >= intersection - 1


def test_shared_transition_norm_is_locked_by_configuration() -> None:
    from pathlib import Path

    from fedact.config.loading import load_production_configuration

    config = load_production_configuration(
        Path(__file__).resolve().parents[3] / "configs" / "fedact.yaml"
    ).values
    generator = np.random.default_rng(3)
    transition = draw_shared_transition(
        generator, config.synthetic.base_sigma, config.synthetic.shared_transition_norm_over_sigma
    )
    expected = config.synthetic.base_sigma * config.synthetic.shared_transition_norm_over_sigma
    assert float(np.linalg.norm(transition.vector)) == pytest.approx(expected)


def test_sparse_private_transition_supports_exactly_ten_percent() -> None:
    generator = np.random.default_rng(4)
    private = draw_private_transition(
        generator,
        norm_over_sigma=0.25,
        sigma=1.0,
        sparsity_mode=PrivateTransitionSparsityMode.TEN_PERCENT_SPARSE,
        sparse_fraction=0.10,
    )
    nonzero = int(np.count_nonzero(private))
    expected = max(1, int(np.floor(0.10 * SYNTHETIC_DIMENSION + 0.5)))
    assert nonzero == expected
    assert float(np.linalg.norm(private)) == pytest.approx(0.25)


def test_effective_support_matches_the_harmonic_formula() -> None:
    assert effective_support(100, 100) == pytest.approx(50.0)


def test_paired_seed_streams_spawn_configured_draw_count() -> None:
    from pathlib import Path

    from fedact.config.loading import load_production_configuration

    config = load_production_configuration(
        Path(__file__).resolve().parents[3] / "configs" / "fedact.yaml"
    ).values
    streams = paired_seed_streams(
        config.synthetic.nested_noise_draws_per_seed,
        tuple(config.seeds.synthetic_generation[:2]),
        tuple(config.seeds.synthetic_noise[:2]),
        0,
    )
    assert len(streams) == config.synthetic.nested_noise_draws_per_seed


def test_principal_angles_and_action_rotation_geometry() -> None:
    generator = np.random.default_rng(5)
    basis = deterministic_orthonormal_basis(generator, 16, 4)
    angles = principal_angles(basis, basis)
    assert angles[0] == pytest.approx(0.0)
    range_direction = np.zeros(16)
    range_direction[0] = 1.0
    null_direction = np.zeros(16)
    null_direction[15] = 1.0
    rotated = action_rotation(range_direction, null_direction, angle_degrees=90.0)
    assert rotated[15] == pytest.approx(1.0)
    score = true_action_score(range_direction, np.ones(16))
    assert score == pytest.approx(1.0)


def test_spectral_conditioning_ratio_computation() -> None:
    singular_values = np.array([4.0, 2.0])
    ratio = spectral_conditioning_ratio(singular_values)
    assert ratio == pytest.approx(0.25)


def test_smoke_validation_report_requires_all_checks_passing() -> None:
    from pathlib import Path

    from fedact.config.loading import load_production_configuration

    root = Path(__file__).resolve().parents[3]
    config = load_production_configuration(root / "configs" / "fedact.yaml").values
    defaults = config.synthetic.defaults
    generator = np.random.default_rng(9)
    requested = nuisance_dimension(defaults.nuisance_dimension_fraction)
    spaces = build_nuisance_spaces(
        generator,
        SYNTHETIC_DIMENSION,
        requested,
        defaults.federation_client_count,
        defaults.federation_geometry,
        defaults.common_intersection_dimension,
    )
    report = run_smoke_validation(
        spaces=spaces,
        transition=draw_shared_transition(
            generator,
            config.synthetic.base_sigma,
            config.synthetic.shared_transition_norm_over_sigma,
        ),
        requested_nuisance_dimension=requested,
        common_intersection=defaults.common_intersection_dimension,
        rank_tolerance=float(config.numerical.rank_clip_epsilon_relative),
        orthonormality_tolerance=float(config.numerical.projection_tie_tolerance),
        seed_pair=[config.seeds.synthetic_generation[0], config.seeds.synthetic_noise[0]],
    )
    assert len(report.results) == 4
    assert all(result.passed for result in report.results[:2])
