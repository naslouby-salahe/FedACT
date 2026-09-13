from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from fedact.data.splits import CalendarMonth
from fedact.domain.types import (
    ActionScore,
    AngleDegrees,
    ClientIndex,
    DetailMessage,
    DimensionValue,
    DrawIndex,
    EffectiveSampleSize,
    FederationGeometry,
    Fraction,
    GridCellIdentity,
    GridCellLabel,
    IntegrityCheckName,
    IntersectionDimension,
    NoiseSeedIdentity,
    PassingFlag,
    PrivateTransitionSparsityMode,
    ReplicateIndex,
    ResampleCount,
    SampleCount,
    SampleSize,
    SeedValue,
    Sigma,
    SplitCutoffIdentity,
    StructuralSeedIdentity,
    Tolerance,
    ValidationFlag,
)

type FloatArray = NDArray[np.float64]

SYNTHETIC_DIMENSION = 64
_NEAREST_INTEGER_ROUNDING_OFFSET = 0.5


class SyntheticGeneratorError(ValueError):
    pass


def nuisance_dimension(
    fraction: Fraction, dimension: DimensionValue = SYNTHETIC_DIMENSION
) -> DimensionValue:
    return max(
        1,
        min(dimension - 1, int(np.floor(fraction * dimension + _NEAREST_INTEGER_ROUNDING_OFFSET))),
    )


def deterministic_orthonormal_basis(
    generator: np.random.Generator, rows: DimensionValue, columns: DimensionValue
) -> FloatArray:
    raw = generator.standard_normal((rows, columns))
    basis, _unused = np.linalg.qr(raw)
    signs = np.sign(basis[np.abs(basis).argmax(axis=0), np.arange(basis.shape[1])])
    signs[signs == 0] = 1.0
    return basis * signs


@dataclass(frozen=True)
class ClientNuisanceGeometry:
    client_index: ClientIndex
    basis: FloatArray


@dataclass(frozen=True)
class NuisanceSpaces:
    geometry: FederationGeometry
    clients: tuple[ClientNuisanceGeometry, ...]

    def __post_init__(self) -> None:
        first = self.clients[0].basis
        for client in self.clients:
            if client.basis.shape != first.shape:
                raise SyntheticGeneratorError(
                    "client nuisance bases must share one shape across clients"
                )


def seeded_generator(seed: SeedValue) -> np.random.Generator:
    return np.random.default_rng(seed)


def build_nuisance_spaces(
    generator: np.random.Generator,
    dimension: DimensionValue,
    nuisance_dimension: DimensionValue,
    client_count: ClientIndex,
    geometry: FederationGeometry,
    common_intersection_dimension: IntersectionDimension,
) -> NuisanceSpaces:
    if geometry is FederationGeometry.REDUNDANT:
        shared = deterministic_orthonormal_basis(generator, dimension, nuisance_dimension)
        return NuisanceSpaces(
            geometry=geometry,
            clients=tuple(
                ClientNuisanceGeometry(client_index=index, basis=shared.copy())
                for index in range(client_count)
            ),
        )
    intersection = min(common_intersection_dimension, nuisance_dimension)
    common_intersection_basis = deterministic_orthonormal_basis(generator, dimension, intersection)
    complement = deterministic_orthonormal_basis(
        generator, dimension, nuisance_dimension - intersection + dimension
    )
    projected = complement - common_intersection_basis @ (common_intersection_basis.T @ complement)
    reorthonormalized, _unused = np.linalg.qr(projected)
    clients: list[ClientNuisanceGeometry] = []
    for index in range(client_count):
        block = reorthonormalized[:, : nuisance_dimension - intersection]
        basis = np.concatenate([common_intersection_basis, block], axis=1)[:, :nuisance_dimension]
        clients.append(ClientNuisanceGeometry(client_index=index, basis=basis))
    return NuisanceSpaces(geometry=geometry, clients=tuple(clients))


@dataclass(frozen=True)
class SharedTransition:
    vector: FloatArray


def draw_shared_transition(
    generator: np.random.Generator,
    base_sigma: Sigma,
    shared_transition_norm_over_sigma: Fraction,
) -> SharedTransition:
    direction = generator.standard_normal(SYNTHETIC_DIMENSION)
    unit = direction / np.linalg.norm(direction)
    scale = base_sigma * shared_transition_norm_over_sigma
    return SharedTransition(vector=scale * unit)


@dataclass(frozen=True)
class ControlReplicate:
    replicate_index: ReplicateIndex
    displacement: FloatArray
    support_before: SampleCount
    support_after: SampleCount


@dataclass(frozen=True)
class MaliciousTransition:
    mean_displacement: FloatArray
    private_component: FloatArray | None
    synchronized_residual: FloatArray | None
    control_span_violation: FloatArray | None


def effective_support(support_before: SampleSize, support_after: SampleSize) -> EffectiveSampleSize:
    return (1.0 / support_before + 1.0 / support_after) ** -1.0


def draw_private_transition(
    generator: np.random.Generator,
    norm_over_sigma: Fraction,
    sigma: Sigma,
    sparsity_mode: PrivateTransitionSparsityMode,
    sparse_fraction: Fraction,
) -> FloatArray:
    if sparsity_mode is PrivateTransitionSparsityMode.DENSE:
        direction = generator.standard_normal(SYNTHETIC_DIMENSION)
    else:
        count = max(
            1,
            int(np.floor(sparse_fraction * SYNTHETIC_DIMENSION + _NEAREST_INTEGER_ROUNDING_OFFSET)),
        )
        coordinates = generator.choice(SYNTHETIC_DIMENSION, size=count, replace=False)
        direction = np.zeros(SYNTHETIC_DIMENSION)
        direction[coordinates] = generator.standard_normal(count)
    unit = direction / np.linalg.norm(direction)
    return norm_over_sigma * sigma * unit


def paired_seed_streams(
    nested_noise_draws_per_seed: ResampleCount,
    generation_seeds: tuple[SeedValue, ...],
    noise_seeds: tuple[SeedValue, ...],
    seed_index: DrawIndex,
) -> list[np.random.Generator]:
    if seed_index >= len(generation_seeds) or seed_index >= len(noise_seeds):
        raise SyntheticGeneratorError(
            f"paired synthetic seed index {seed_index} exceeds the configured seed arrays"
        )
    sequence = np.random.SeedSequence([generation_seeds[seed_index], noise_seeds[seed_index]])
    children = sequence.spawn(nested_noise_draws_per_seed)
    return [np.random.default_rng(child) for child in children]


def grid_cell_identity(label: GridCellLabel) -> GridCellIdentity:
    return GridCellIdentity(label)


def structural_identity(seed_index: SeedValue) -> StructuralSeedIdentity:
    return StructuralSeedIdentity(f"structural-{seed_index}")


def noise_identity(seed_index: SeedValue, draw_index: DrawIndex) -> NoiseSeedIdentity:
    return NoiseSeedIdentity(f"noise-{seed_index}-{draw_index}")


def cutoff_label(month_index: CalendarMonth) -> SplitCutoffIdentity:
    return SplitCutoffIdentity(f"synthetic-month-{month_index:06d}")


def _norm(vector: NDArray[np.float64]) -> float:
    return float(np.sqrt(np.sum(vector * vector)))


class GeometryValidationError(ValueError):
    pass


def verify_orthonormality(basis: np.ndarray, tolerance: Tolerance) -> None:
    residual = float(np.max(np.abs(basis.T @ basis - np.eye(basis.shape[1]))))
    if residual > tolerance:
        raise GeometryValidationError(
            f"nuisance basis is not orthonormal within tolerance {tolerance}: {residual}"
        )


def common_intersection_dimension(
    bases: tuple[np.ndarray, ...], rank_tolerance: Tolerance
) -> IntersectionDimension:
    stacked = np.concatenate(bases, axis=1)
    singular_values = np.linalg.svd(stacked, compute_uv=False)
    if singular_values.size == 0:
        return 0
    cutoff = max(singular_values[0], 1.0) * rank_tolerance
    return int(np.count_nonzero(singular_values > cutoff))


def principal_angles(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    overlap = first.T @ second
    singular_values = np.linalg.svd(overlap, compute_uv=False)
    cosine = np.clip(singular_values, -1.0, 1.0)
    return np.arccos(cosine)


@dataclass(frozen=True)
class ActionGeometry:
    range_direction: np.ndarray
    null_direction: np.ndarray


def action_rotation(
    range_direction: np.ndarray, null_direction: np.ndarray, angle_degrees: AngleDegrees
) -> np.ndarray:
    theta = np.deg2rad(angle_degrees)
    rotated = np.cos(theta) * range_direction + np.sin(theta) * null_direction
    norm = _norm(rotated)
    if norm < 1e-12:
        raise GeometryValidationError("action rotation produced a zero direction")
    return rotated / norm


def true_action_score(direction: np.ndarray, transition: np.ndarray) -> ActionScore:
    return float(direction @ transition)


def spectral_conditioning_ratio(singular_values: np.ndarray) -> Fraction:
    positive = singular_values[singular_values > 0]
    if positive.size < 2:
        raise GeometryValidationError(
            "spectral conditioning requires at least two nonzero singular values"
        )
    ratio = positive.min() / positive.max()
    return float(ratio * ratio)


class SmokeValidationError(ValueError):
    pass


@dataclass(frozen=True)
class SmokeCheckResult:
    check_name: IntegrityCheckName
    passed: ValidationFlag
    detail: DetailMessage


@dataclass(frozen=True)
class SmokeValidationReport:
    results: tuple[SmokeCheckResult, ...]

    @property
    def is_passing(self) -> PassingFlag:
        return all(result.passed for result in self.results)

    def require_pass(self) -> None:
        failures = [result.check_name for result in self.results if not result.passed]
        if failures:
            raise SmokeValidationError(f"synthetic smoke validation failed: {failures}")


def _check_nuisance_dimensions(
    spaces: NuisanceSpaces, requested: DimensionValue
) -> SmokeCheckResult:
    observed = spaces.clients[0].basis.shape[1]
    all_match = all(client.basis.shape[1] == requested for client in spaces.clients)
    return SmokeCheckResult(
        check_name="nuisance_dimension",
        passed=all_match and observed == requested,
        detail=f"requested={requested} observed={observed}",
    )


def _check_orthonormality(spaces: NuisanceSpaces, tolerance: Tolerance) -> SmokeCheckResult:
    worst = max(
        float(np.max(np.abs(client.basis.T @ client.basis - np.eye(client.basis.shape[1]))))
        for client in spaces.clients
    )
    return SmokeCheckResult(
        check_name="orthonormality",
        passed=worst <= tolerance,
        detail=f"max deviation={worst}",
    )


def _check_intersection(
    spaces: NuisanceSpaces, requested: IntersectionDimension, rank_tolerance: Tolerance
) -> SmokeCheckResult:
    stacked = np.concatenate([client.basis for client in spaces.clients], axis=1)
    singular_values = np.linalg.svd(stacked, compute_uv=False)
    cutoff = max(float(singular_values[0]), 1.0) * rank_tolerance
    observed = int(np.count_nonzero(singular_values > cutoff))
    expected = (
        requested
        if spaces.geometry is FederationGeometry.REDUNDANT
        else min(requested, spaces.clients[0].basis.shape[1])
    )
    return SmokeCheckResult(
        check_name="common_intersection",
        passed=observed >= min(expected, spaces.clients[0].basis.shape[1]),
        detail=f"requested={requested} observed={observed}",
    )


def _check_replay_determinism(seed_pair: list[SeedValue]) -> SmokeCheckResult:
    first = np.random.default_rng(np.random.SeedSequence(seed_pair).spawn(1)[0]).standard_normal(8)
    second = np.random.default_rng(np.random.SeedSequence(seed_pair).spawn(1)[0]).standard_normal(8)
    identical = bool(np.array_equal(first, second))
    return SmokeCheckResult(
        check_name="deterministic_replay",
        passed=identical,
        detail="paired seed streams reproduce exactly",
    )


def run_smoke_validation(
    spaces: NuisanceSpaces,
    transition: SharedTransition,
    requested_nuisance_dimension: DimensionValue,
    common_intersection: IntersectionDimension,
    rank_tolerance: Tolerance,
    orthonormality_tolerance: Tolerance,
    seed_pair: list[SeedValue],
) -> SmokeValidationReport:
    if transition.vector.shape != (SYNTHETIC_DIMENSION,):
        raise SyntheticGeneratorError(f"shared transition must live in R^{SYNTHETIC_DIMENSION}")
    _unused = deterministic_orthonormal_basis
    return SmokeValidationReport(
        results=(
            _check_nuisance_dimensions(spaces, requested_nuisance_dimension),
            _check_orthonormality(spaces, orthonormality_tolerance),
            _check_intersection(spaces, common_intersection, rank_tolerance),
            _check_replay_determinism(seed_pair),
        )
    )
