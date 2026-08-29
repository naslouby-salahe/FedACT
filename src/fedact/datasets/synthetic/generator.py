from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, NewType

import numpy as np
from numpy.typing import NDArray
from pydantic import Field

from fedact.config.models import (
    FederationGeometry,
    PrivateTransitionSparsityMode,
    SyntheticConfig,
)
from fedact.datasets.chronology import CalendarMonth
from fedact.domain.records import SplitCutoffIdentity
from fedact.domain.types import DrawIndex, GridCellLabel, ReplicateIndex, SampleCount, SeedValue

FloatArray = NDArray[np.float64]
GridCellIdentity = NewType("GridCellIdentity", str)
StructuralSeedIdentity = NewType("StructuralSeedIdentity", str)
NoiseSeedIdentity = NewType("NoiseSeedIdentity", str)

SYNTHETIC_DIMENSION = 64

SeedIndex = NewType("SeedIndex", int)
NuisanceFraction = Annotated[float, Field(ge=0.0, le=1.0)]
Dimension = Annotated[int, Field(ge=1)]
ClientIndex = Annotated[int, Field(ge=0)]
SigmaScale = Annotated[float, Field(ge=0.0)]
SparseFraction = Annotated[float, Field(ge=0.0, le=1.0)]


class SyntheticGeneratorError(ValueError):
    pass


def nuisance_dimension(
    fraction: NuisanceFraction, dimension: Dimension = SYNTHETIC_DIMENSION
) -> Dimension:
    return max(1, min(dimension - 1, int(np.floor(fraction * dimension + 0.5))))


def deterministic_orthonormal_basis(
    generator: np.random.Generator, rows: Dimension, columns: Dimension
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
    dimension: Dimension,
    nuisance_dimension: Dimension,
    client_count: ClientIndex,
    geometry: FederationGeometry,
    common_intersection_dimension: Dimension,
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
    common = deterministic_orthonormal_basis(generator, dimension, intersection)
    complement = deterministic_orthonormal_basis(
        generator, dimension, nuisance_dimension - intersection + dimension
    )
    projected = complement - common @ (common.T @ complement)
    reorthonormalized, _unused = np.linalg.qr(projected)
    clients: list[ClientNuisanceGeometry] = []
    for index in range(client_count):
        block = reorthonormalized[:, : nuisance_dimension - intersection]
        basis = np.concatenate([common, block], axis=1)[:, :nuisance_dimension]
        clients.append(ClientNuisanceGeometry(client_index=index, basis=basis))
    return NuisanceSpaces(geometry=geometry, clients=tuple(clients))


@dataclass(frozen=True)
class SharedTransition:
    vector: FloatArray


def draw_shared_transition(
    generator: np.random.Generator, config: SyntheticConfig
) -> SharedTransition:
    direction = generator.standard_normal(SYNTHETIC_DIMENSION)
    unit = direction / np.linalg.norm(direction)
    scale = config.base_sigma * config.shared_transition_norm_over_sigma
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


SupportSide = Annotated[int, Field(ge=1)]
EffectiveSupport = Annotated[float, Field(gt=0.0)]


def effective_support(support_before: SupportSide, support_after: SupportSide) -> EffectiveSupport:
    return (1.0 / support_before + 1.0 / support_after) ** -1.0


def draw_private_transition(
    generator: np.random.Generator,
    norm_over_sigma: SigmaScale,
    sigma: SigmaScale,
    sparsity_mode: PrivateTransitionSparsityMode,
    sparse_fraction: SparseFraction,
) -> FloatArray:
    if sparsity_mode is PrivateTransitionSparsityMode.DENSE:
        direction = generator.standard_normal(SYNTHETIC_DIMENSION)
    else:
        count = max(1, int(np.floor(sparse_fraction * SYNTHETIC_DIMENSION + 0.5)))
        coordinates = generator.choice(SYNTHETIC_DIMENSION, size=count, replace=False)
        direction = np.zeros(SYNTHETIC_DIMENSION)
        direction[coordinates] = generator.standard_normal(count)
    unit = direction / np.linalg.norm(direction)
    return norm_over_sigma * sigma * unit


def paired_seed_streams(
    config: SyntheticConfig,
    generation_seeds: tuple[Annotated[int, Field(ge=0)], ...],
    noise_seeds: tuple[Annotated[int, Field(ge=0)], ...],
    seed_index: Annotated[int, Field(ge=0)],
) -> list[np.random.Generator]:
    if seed_index >= len(generation_seeds) or seed_index >= len(noise_seeds):
        raise SyntheticGeneratorError(
            f"paired synthetic seed index {seed_index} exceeds the configured seed arrays"
        )
    sequence = np.random.SeedSequence([generation_seeds[seed_index], noise_seeds[seed_index]])
    children = sequence.spawn(config.nested_noise_draws_per_seed)
    return [np.random.default_rng(child) for child in children]


def grid_cell_identity(label: GridCellLabel) -> GridCellIdentity:
    return GridCellIdentity(label)


def structural_identity(seed_index: SeedValue) -> StructuralSeedIdentity:
    return StructuralSeedIdentity(f"structural-{seed_index}")


def noise_identity(seed_index: SeedValue, draw_index: DrawIndex) -> NoiseSeedIdentity:
    return NoiseSeedIdentity(f"noise-{seed_index}-{draw_index}")


def cutoff_label(month_index: CalendarMonth) -> SplitCutoffIdentity:
    return SplitCutoffIdentity(f"synthetic-month-{int(month_index):06d}")
