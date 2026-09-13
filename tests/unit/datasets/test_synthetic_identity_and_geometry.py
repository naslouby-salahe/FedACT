from __future__ import annotations

import numpy as np
import pytest

from fedact.data.splits import calendar_month
from fedact.data.synthetic import (
    GeometryValidationError,
    SmokeCheckResult,
    SmokeValidationError,
    SmokeValidationReport,
    action_rotation,
    common_intersection_dimension,
    cutoff_label,
    grid_cell_identity,
    noise_identity,
    paired_seed_streams,
    spectral_conditioning_ratio,
    structural_identity,
    true_action_score,
    verify_orthonormality,
)

DRAWS_PER_SEED = 3
GENERATION_SEEDS = (11, 22)
NOISE_SEEDS = (33, 44)
TOLERANCE = 1.0e-9
RANK_TOLERANCE = 1.0e-6


def test_paired_seed_streams_spawn_the_requested_number_of_draws() -> None:
    streams = paired_seed_streams(DRAWS_PER_SEED, GENERATION_SEEDS, NOISE_SEEDS, 0)
    assert len(streams) == DRAWS_PER_SEED
    assert all(isinstance(stream, np.random.Generator) for stream in streams)


def test_paired_seed_streams_are_reproducible_for_a_seed_index() -> None:
    first = paired_seed_streams(DRAWS_PER_SEED, GENERATION_SEEDS, NOISE_SEEDS, 1)
    second = paired_seed_streams(DRAWS_PER_SEED, GENERATION_SEEDS, NOISE_SEEDS, 1)
    assert [stream.random() for stream in first] == [stream.random() for stream in second]


def test_paired_seed_streams_reject_an_out_of_range_index() -> None:
    with pytest.raises(Exception, match="exceeds the configured seed arrays"):
        paired_seed_streams(DRAWS_PER_SEED, GENERATION_SEEDS, NOISE_SEEDS, 5)


def test_identity_labels_are_deterministic_and_distinct() -> None:
    assert grid_cell_identity("cell-3") == "cell-3"
    assert structural_identity(2) == "structural-2"
    assert noise_identity(2, 4) == "noise-2-4"
    assert cutoff_label(calendar_month(7)) == "synthetic-month-000007"


def test_orthonormal_bases_pass_verification() -> None:
    verify_orthonormality(np.eye(3), TOLERANCE)


def test_non_orthonormal_bases_are_rejected() -> None:
    with pytest.raises(GeometryValidationError, match="not orthonormal"):
        verify_orthonormality(np.full((2, 2), 0.5), TOLERANCE)


def test_common_intersection_dimension_of_identical_bases_is_their_rank() -> None:
    basis = np.eye(2)
    assert common_intersection_dimension((basis, basis), RANK_TOLERANCE) == 2


def test_action_rotation_of_zero_degrees_returns_the_range_direction() -> None:
    rotated = action_rotation(np.array([1.0, 0.0]), np.array([0.0, 1.0]), 0.0)
    assert np.allclose(rotated, np.array([1.0, 0.0]))


def test_action_rotation_returns_a_unit_direction() -> None:
    rotated = action_rotation(np.array([1.0, 0.0]), np.array([0.0, 1.0]), 90.0)
    assert np.linalg.norm(rotated) == pytest.approx(1.0)


def test_action_rotation_rejects_a_cancelling_pair_of_directions() -> None:
    with pytest.raises(GeometryValidationError, match="zero direction"):
        action_rotation(np.array([1.0, 0.0]), np.array([-1.0, 0.0]), 45.0)


def test_true_action_score_is_the_projection_onto_the_transition() -> None:
    assert true_action_score(np.array([1.0, 0.0]), np.array([3.0, 4.0])) == pytest.approx(3.0)


def test_spectral_conditioning_requires_two_nonzero_singular_values() -> None:
    with pytest.raises(GeometryValidationError, match="at least two nonzero"):
        spectral_conditioning_ratio(np.array([1.0, 0.0, 0.0]))


def test_spectral_conditioning_is_the_squared_smallest_over_largest_ratio() -> None:
    assert spectral_conditioning_ratio(np.array([4.0, 2.0])) == pytest.approx(0.25)


def _check(name: str, passed: bool) -> SmokeCheckResult:
    return SmokeCheckResult(
        check_name=name,
        passed=passed,
        detail="detail",
    )


def test_smoke_report_passes_when_every_check_passes() -> None:
    report = SmokeValidationReport(results=(_check("a", True), _check("b", True)))
    assert report.is_passing is True
    report.require_pass()


def test_smoke_report_raises_when_a_check_fails() -> None:
    report = SmokeValidationReport(results=(_check("a", True), _check("b", False)))
    assert report.is_passing is False
    with pytest.raises(SmokeValidationError, match="synthetic smoke validation failed"):
        report.require_pass()
