from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import numpy as np
from numpy.typing import NDArray
from pydantic import Field

FloatArray = NDArray[np.float64]
RankCandidate = Annotated[int, Field(ge=1)]
Dimension = Annotated[int, Field(ge=1)]
ReplicateCount = Annotated[int, Field(ge=2)]
ConfiguredMaximum = Annotated[int, Field(ge=1)]
RatioValue = Annotated[float, Field(ge=0.0)]
Requirement = Annotated[float, Field(gt=0.0)]
ClipRelative = Annotated[float, Field(gt=0.0)]
ScaleFloor = Annotated[float, Field(gt=0.0)]
RegularizationCoefficient = Annotated[float, Field(ge=0.0)]
StabilityFraction = Annotated[float, Field(gt=0.0, le=1.0)]


@dataclass(frozen=True)
class NuisanceEstimate:
    basis: FloatArray
    selected_rank: int
    eigengap_ratio: float


def weighted_covariance(
    displacements: tuple[FloatArray, ...], weights: tuple[float, ...]
) -> FloatArray:
    if len(displacements) != len(weights) or not displacements:
        raise ValueError("covariance estimation requires aligned displacements and weights")
    total = float(sum(weights))
    if total <= 0.0:
        raise ValueError("weights must carry positive mass")
    stacked: FloatArray = np.stack(displacements)
    mean = (stacked * np.array(weights)[:, None]).sum(axis=0) / total
    centered = stacked - mean
    weighted = centered * np.sqrt(np.array(weights))[:, None]
    return (weighted.T @ weighted) / total


def admissible_rank(
    dimension: Dimension, replicates: ReplicateCount, configured_maximum: ConfiguredMaximum
) -> RankCandidate:
    return min(dimension - 1, replicates - 1, configured_maximum)


def eigengap_ratio(
    eigenvalues: FloatArray, rank: RankCandidate, clip_relative: ClipRelative, floor: ScaleFloor
) -> RatioValue:
    numerator = float(eigenvalues[rank - 1])
    denominator = max(float(eigenvalues[rank]), clip_relative * float(eigenvalues[0]), floor)
    if denominator <= 0.0:
        raise ValueError("eigengap denominator must be positive")
    value: RatioValue = numerator / denominator
    return value


def select_rank_by_eigengap(
    eigenvalues: FloatArray,
    maximum_admissible: ConfiguredMaximum,
    calibrated_requirement: Requirement,
    clip_relative: ClipRelative,
    floor: ScaleFloor,
) -> RankCandidate | None:
    selected: int | None = None
    for rank in range(1, maximum_admissible + 1):
        ratio = eigengap_ratio(eigenvalues, rank, clip_relative, floor)
        if ratio >= calibrated_requirement:
            selected = rank
    return selected


def regularized_covariance(
    raw: FloatArray, coefficient: RegularizationCoefficient, floor: ScaleFloor
) -> FloatArray:
    dimension = raw.shape[0]
    eta = max(floor, coefficient * float(np.trace(raw)) / dimension)
    result: FloatArray = raw + eta * np.eye(dimension)
    return result


def is_rank_stable(
    resample_ranks: tuple[RankCandidate, ...],
    full_sample_rank: RankCandidate,
    minimum_fraction: StabilityFraction,
) -> bool:
    if not resample_ranks:
        raise ValueError("rank stability requires at least one bootstrap resample")
    agreeing = sum(1 for rank in resample_ranks if rank == full_sample_rank)
    return (agreeing / len(resample_ranks)) >= minimum_fraction
