from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import NewType

import numpy as np
import torch

from fedact.domain.types import (
    ClientIndex,
    CoordinateValue,
    DiagnosisMessage,
    IterationCount,
    NormValue,
    SampleCount,
    ThresholdValue,
)

ClientIdentifier = NewType("ClientIdentifier", str)


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
    subspace: torch.Tensor
    uncertainty_radius: ThresholdValue
    support_before: SampleCount
    support_after: SampleCount
    control_displacement_norm: NormValue
    beta: ThresholdValue
    control_quality_diagnostics: DiagnosisMessage


def effective_support(
    *args: SampleCount | Sequence[SampleCount] | tuple[SampleCount, SampleCount],
) -> CoordinateValue:
    if len(args) == 2 and isinstance(args[0], (int, float)) and isinstance(args[1], (int, float)):
        n1, n2 = float(args[0]), float(args[1])
        return float(n1 * n2 / (n1 + n2)) if (n1 + n2) > 0 else 0.0
    if len(args) == 1 and isinstance(args[0], tuple) and len(args[0]) == 2:
        n1, n2 = float(args[0][0]), float(args[0][1])
        return float(n1 * n2 / (n1 + n2)) if (n1 + n2) > 0 else 0.0
    if len(args) == 1 and isinstance(args[0], (list, tuple)):
        return float(sum(args[0]))
    return float(sum(float(a) for a in args if isinstance(a, (int, float))))


def geometric_median(
    points: np.ndarray | Sequence[np.ndarray | torch.Tensor],
    tolerance: ThresholdValue = 1e-9,
    maximum_iterations: IterationCount = 500,
) -> np.ndarray:
    if isinstance(points, (list, tuple)):
        arr = np.asarray([np.asarray(p, dtype=np.float64) for p in points], dtype=np.float64)
    else:
        arr = np.asarray(points, dtype=np.float64)
    if arr.ndim == 1:
        return arr
    if arr.shape[0] == 1:
        return arr[0]

    current = np.mean(arr, axis=0)
    for _ in range(maximum_iterations):
        diffs = arr - current
        distances = np.linalg.norm(diffs, axis=1)
        zero_dist = distances < 1e-12
        if np.any(zero_dist):
            return arr[np.nonzero(zero_dist)[0][0]]
        weights = 1.0 / distances
        weights /= np.sum(weights)
        next_val = np.sum(arr * weights[:, None], axis=0)
        if np.linalg.norm(next_val - current) < tolerance:
            return next_val
        current = next_val
    return current


def weighted_control_center(
    controls: Sequence[np.ndarray | torch.Tensor],
    weights: Sequence[CoordinateValue | tuple[SampleCount, SampleCount]] | None = None,
) -> np.ndarray:
    if not controls:
        return np.zeros(1)
    arrs = [np.array(c) if isinstance(c, torch.Tensor) else c for c in controls]
    if weights is None:
        return np.mean(arrs, axis=0)

    scalar_weights: list[float] = []
    for w in weights:
        if isinstance(w, tuple) and len(w) == 2:
            n1, n2 = w
            sw = float(n1 * n2 / (n1 + n2)) if (n1 + n2) > 0 else 0.0
        else:
            sw = float(w)
        scalar_weights.append(sw)

    total_w = sum(scalar_weights)
    if total_w < 1e-12:
        return np.mean(arrs, axis=0)

    norm_w = [sw / total_w for sw in scalar_weights]
    return np.sum([p * nw for p, nw in zip(arrs, norm_w, strict=True)], axis=0)


def observed_nuisance_amplitude(
    displacements: Sequence[np.ndarray | torch.Tensor],
    supports: Sequence[CoordinateValue | tuple[SampleCount, SampleCount]] | None = None,
    quantile: ThresholdValue = 0.95,
) -> CoordinateValue:
    arrs = [np.array(d) if isinstance(d, torch.Tensor) else d for d in displacements]
    norms = [float(np.linalg.norm(a)) for a in arrs]
    if supports is not None and len(supports) == len(norms):
        active_norms: list[float] = []
        for n, s in zip(norms, supports, strict=False):
            val = float(s[0] + s[1]) if isinstance(s, tuple) else float(s)
            if val > 0:
                active_norms.append(float(n))
        norms = active_norms
    return float(np.quantile(norms, quantile)) if norms else 0.0


def later_real_proxy(
    pre_means: Sequence[np.ndarray | torch.Tensor],
    post_means: Sequence[np.ndarray | torch.Tensor],
    pre_supports: Sequence[SampleCount],
    post_supports: Sequence[SampleCount],
) -> np.ndarray:
    diffs = [
        np.array(post) - np.array(pre) for pre, post in zip(pre_means, post_means, strict=True)
    ]
    eff_supports = [
        n_pre * n_post / (n_pre + n_post) if (n_pre + n_post) > 0 else 0
        for n_pre, n_post in zip(pre_supports, post_supports, strict=True)
    ]
    total_supp = sum(eff_supports)
    if total_supp < 1e-12:
        return np.mean(diffs, axis=0)
    return np.sum(
        [d * (s / total_supp) for d, s in zip(diffs, eff_supports, strict=True)],
        axis=0,
    )


@dataclass(frozen=True)
class ClientAbstention:
    reason: AbstentionReason = AbstentionReason.ABSTAIN_NO_USABLE_CONTROL


def leave_one_client_reference(
    transmissions: Sequence[ClientTransmission],
    excluded_index: ClientIndex,
) -> ClientTransmission:
    remaining = [t for i, t in enumerate(transmissions) if i != excluded_index]
    if not remaining:
        return transmissions[0]
    return remaining[0]
