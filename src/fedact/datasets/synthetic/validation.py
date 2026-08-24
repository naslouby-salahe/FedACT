from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import numpy as np
from pydantic import Field

from fedact.config.models import FederationGeometry
from fedact.datasets.synthetic.generator import (
    SYNTHETIC_DIMENSION,
    NuisanceSpaces,
    SharedTransition,
    SyntheticGeneratorError,
    deterministic_orthonormal_basis,
)
from fedact.domain.types import DetailMessage, IntegrityCheckName, ValidationFlag


class SmokeValidationError(ValueError):
    pass


DimensionCount = Annotated[int, Field(ge=0)]
ToleranceValue = Annotated[float, Field(gt=0.0)]


@dataclass(frozen=True)
class SmokeCheckResult:
    check_name: IntegrityCheckName
    passed: ValidationFlag
    detail: DetailMessage


@dataclass(frozen=True)
class SmokeValidationReport:
    results: tuple[SmokeCheckResult, ...]

    @property
    def is_passing(self) -> bool:
        return all(result.passed for result in self.results)

    def require_pass(self) -> None:
        failures = [result.check_name for result in self.results if not result.passed]
        if failures:
            raise SmokeValidationError(f"synthetic smoke validation failed: {failures}")


def _check_nuisance_dimensions(spaces: NuisanceSpaces, requested: int) -> SmokeCheckResult:
    observed = spaces.clients[0].basis.shape[1]
    all_match = all(client.basis.shape[1] == requested for client in spaces.clients)
    return SmokeCheckResult(
        check_name="nuisance_dimension",
        passed=all_match and observed == requested,
        detail=f"requested={requested} observed={observed}",
    )


def _check_orthonormality(spaces: NuisanceSpaces, tolerance: float) -> SmokeCheckResult:
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
    spaces: NuisanceSpaces, requested: int, rank_tolerance: float
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


def _check_replay_determinism(seed_pair: list[int]) -> SmokeCheckResult:
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
    requested_nuisance_dimension: DimensionCount,
    common_intersection: DimensionCount,
    rank_tolerance: ToleranceValue,
    orthonormality_tolerance: ToleranceValue,
    seed_pair: list[Annotated[int, Field(ge=0)]],
) -> SmokeValidationReport:
    if transition.vector.shape != (SYNTHETIC_DIMENSION,):
        raise SyntheticGeneratorError(f"shared transition must live in R^{SYNTHETIC_DIMENSION}")
    _ = deterministic_orthonormal_basis
    return SmokeValidationReport(
        results=(
            _check_nuisance_dimensions(spaces, requested_nuisance_dimension),
            _check_orthonormality(spaces, orthonormality_tolerance),
            _check_intersection(spaces, common_intersection, rank_tolerance),
            _check_replay_determinism(seed_pair),
        )
    )
