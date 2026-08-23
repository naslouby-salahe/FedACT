from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, NewType

import numpy as np
from numpy.typing import NDArray
from pydantic import Field

from fedact.domain.records import SplitCutoffIdentity

FloatArray = NDArray[np.float64]
ClientIdentifier = NewType("ClientIdentifier", str)

SideSupport = Annotated[int, Field(ge=1)]
EffectiveSupport = Annotated[float, Field(gt=0.0)]
NuisanceAmplitude = Annotated[float, Field(ge=0.0)]
QuantileLevel = Annotated[float, Field(gt=0.0, le=1.0)]
ConvergenceTolerance = Annotated[float, Field(gt=0.0)]
IterationLimit = Annotated[int, Field(ge=1)]


class AbstentionReason(StrEnum):
    ABSTAIN_NO_USABLE_CONTROL = "ABSTAIN_NO_USABLE_CONTROL"
    ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT = "ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT"
    ABSTAIN_INSUFFICIENT_CONTROL_SUPPORT = "ABSTAIN_INSUFFICIENT_CONTROL_SUPPORT"
    ABSTAIN_INSUFFICIENT_PRIVATE_ALLOWANCE_HISTORY = (
        "ABSTAIN_INSUFFICIENT_PRIVATE_ALLOWANCE_HISTORY"
    )
    ABSTAIN_UNSTABLE_NUISANCE_RANK = "ABSTAIN_UNSTABLE_NUISANCE_RANK"
    ABSTAIN_WEAK_EIGENGAP = "ABSTAIN_WEAK_EIGENGAP"
    ABSTAIN_CONTROL_RECONSTRUCTION_FAILURE = "ABSTAIN_CONTROL_RECONSTRUCTION_FAILURE"
    ABSTAIN_FEASIBLE_SET_INCONSISTENT = "ABSTAIN_FEASIBLE_SET_INCONSISTENT"
    ABSTAIN_INSUFFICIENT_TEMPORAL_HISTORY = "ABSTAIN_INSUFFICIENT_TEMPORAL_HISTORY"
    ABSTAIN_FORECAST_SET_TOO_WIDE = "ABSTAIN_FORECAST_SET_TOO_WIDE"
    ABSTAIN_NO_CERTIFIED_ACTION = "ABSTAIN_NO_CERTIFIED_ACTION"
    ABSTAIN_OPERATOR_COVERAGE_INSUFFICIENT = "ABSTAIN_OPERATOR_COVERAGE_INSUFFICIENT"
    ABSTAIN_SYNCHRONIZED_NUISANCE_RISK = "ABSTAIN_SYNCHRONIZED_NUISANCE_RISK"
    ABSTAIN_SINGLE_CLIENT_CERTIFICATE_DOMINANCE = "ABSTAIN_SINGLE_CLIENT_CERTIFICATE_DOMINANCE"


@dataclass(frozen=True)
class ClientTransmission:
    client_id: ClientIdentifier
    nuisance_basis: FloatArray
    transition_vector: FloatArray
    covariance: FloatArray
    support_before: int
    support_after: int
    control_displacement_norm: float
    beta: float
    control_quality_diagnostics: str


@dataclass(frozen=True)
class ClientAbstention:
    client_id: ClientIdentifier
    cutoff_identity: SplitCutoffIdentity
    reason: AbstentionReason


def effective_support(support_before: SideSupport, support_after: SideSupport) -> EffectiveSupport:
    value: EffectiveSupport = (1.0 / support_before + 1.0 / support_after) ** -1.0
    return value


def weighted_control_center(
    displacements: tuple[FloatArray, ...], supports: tuple[tuple[int, int], ...]
) -> FloatArray:
    if len(displacements) != len(supports):
        raise ValueError("each control replicate needs exactly one support pair")
    weights = np.array([effective_support(before, after) for before, after in supports])
    total = float(weights.sum())
    if total <= 0.0:
        raise ValueError("control replicates carry no effective support")
    normalized = weights / total
    stacked = np.stack(displacements)
    return (stacked * normalized[:, None]).sum(axis=0)


def observed_nuisance_amplitude(
    displacements: tuple[FloatArray, ...],
    supports: tuple[tuple[int, int], ...],
    quantile: QuantileLevel,
) -> NuisanceAmplitude:
    center = weighted_control_center(displacements, supports)
    norms = [float(np.linalg.norm(displacement - center)) for displacement in displacements]
    value: NuisanceAmplitude = float(np.quantile(norms, quantile, method="linear"))
    return value


def geometric_median(
    points: FloatArray, tolerance: ConvergenceTolerance, maximum_iterations: IterationLimit
) -> FloatArray:
    if not points.size:
        raise ValueError("geometric median requires at least one point")
    current = points.mean(axis=0)
    for _ in range(maximum_iterations):
        distances = np.linalg.norm(points - current, axis=1)
        nonzero = distances > tolerance
        if not np.any(nonzero):
            break
        weights = 1.0 / distances[nonzero]
        updated = (points[nonzero] * weights[:, None]).sum(axis=0) / weights.sum()
        converged = float(np.linalg.norm(updated - current)) < tolerance
        current = updated
        if converged:
            break
    return current


def leave_one_client_reference(
    vectors: FloatArray,
    tolerance: ConvergenceTolerance,
    maximum_iterations: IterationLimit,
) -> FloatArray:
    return geometric_median(vectors, tolerance, maximum_iterations)


def later_real_proxy(
    pre_means: tuple[FloatArray, ...],
    post_means: tuple[FloatArray, ...],
    pre_supports: tuple[int, ...],
    post_supports: tuple[int, ...],
) -> FloatArray:
    numerators: list[FloatArray] = []
    weights: list[float] = []
    for pre_mean, post_mean, n_pre, n_post in zip(
        pre_means, post_means, pre_supports, post_supports, strict=True
    ):
        weight = (1.0 / n_pre + 1.0 / n_post) ** -1
        weights.append(weight)
        numerators.append(weight * (post_mean - pre_mean))
    total: float = sum(weights)
    stacked: FloatArray = np.stack(numerators)
    return stacked.sum(axis=0) / total
