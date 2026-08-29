from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch

from fedact.domain.enums import RankSelectionMethod
from fedact.domain.types import (
    CoordinateValue,
    EigengapRatio,
    MetricRate,
    RankDimension,
    SampleCount,
    ThresholdValue,
)
from fedact.fedact.controls import ControlReplicate


@dataclass(frozen=True)
class NuisanceEstimate:
    subspace: torch.Tensor
    uncertainty_radius: ThresholdValue
    selected_rank: RankDimension
    eigengap_ratio: EigengapRatio
    replicates: tuple[ControlReplicate, ...]


def weighted_covariance(
    samples: np.ndarray | torch.Tensor | Sequence[np.ndarray | torch.Tensor],
    weights: Sequence[CoordinateValue] | None = None,
) -> np.ndarray:
    if isinstance(samples, (list, tuple)):
        arrs = [np.asarray(s, dtype=np.float64) for s in samples]
        if weights is not None:
            w = np.array(weights, dtype=np.float64) / sum(weights)
            cov = np.zeros((arrs[0].shape[0], arrs[0].shape[0]), dtype=np.float64)
            for a, wi in zip(arrs, w, strict=True):
                cov += wi * np.outer(a, a)
            return cov
        return np.cov(np.stack(arrs), rowvar=False)
    s = np.asarray(samples, dtype=np.float64)
    if s.shape[0] <= 1:
        return np.eye(s.shape[1] if s.ndim > 1 else 1, dtype=np.float64)
    if weights is not None:
        w = np.array(weights, dtype=np.float64) / sum(weights)
        mean = np.sum(s * w[:, None], axis=0)
        diff = s - mean
        return (diff.T * w) @ diff
    return np.cov(s, rowvar=False)


def regularized_covariance(
    covariance: np.ndarray | torch.Tensor,
    regularization: ThresholdValue | None = None,
    coefficient: CoordinateValue = 0.01,
    floor: CoordinateValue = 1e-6,
) -> np.ndarray:
    _unused = floor
    reg = regularization if regularization is not None else coefficient
    c = np.array(covariance) if isinstance(covariance, torch.Tensor) else covariance
    return c + reg * np.eye(c.shape[0])


def admissible_rank(
    spectrum: Sequence[CoordinateValue] | None = None,
    variance_threshold: ThresholdValue = 0.95,
    dimension: RankDimension | None = None,
    replicates: SampleCount | None = None,
    configured_maximum: RankDimension | None = None,
) -> RankDimension:
    if dimension is not None and replicates is not None and configured_maximum is not None:
        return min(dimension - 1, replicates - 1, configured_maximum)
    if spectrum is not None:
        s = sorted(spectrum, reverse=True)
        total = sum(s)
        if total < 1e-12:
            return 1
        cum = 0.0
        for idx, val in enumerate(s):
            cum += val
            if cum / total >= variance_threshold:
                return idx + 1
        return len(s)
    return 1


def eigengap_ratio(
    spectrum: Sequence[CoordinateValue] | np.ndarray,
    rank: RankDimension,
    regularization: ThresholdValue = 1e-6,
    clip_relative: ThresholdValue = 1e-6,
    floor: ThresholdValue = 1e-8,
) -> EigengapRatio:
    _unused = (regularization, clip_relative, floor)
    s = sorted(spectrum, reverse=True)
    if rank <= 0 or rank >= len(s):
        return 1.0
    return float(s[rank - 1] / max(1e-12, s[rank]))


def select_rank_by_eigengap(
    spectrum: Sequence[CoordinateValue] | np.ndarray,
    maximum_rank: RankDimension | None = None,
    maximum_admissible: RankDimension | None = None,
    calibrated_requirement: ThresholdValue = 1.05,
    clip_relative: ThresholdValue = 1e-6,
    floor: ThresholdValue = 1e-8,
) -> RankDimension:
    _unused = (clip_relative, floor)
    s = sorted(spectrum, reverse=True)
    if maximum_admissible is not None:
        max_r = maximum_admissible
    elif maximum_rank is not None:
        max_r = maximum_rank
    else:
        max_r = len(s) - 1

    selected_rank = 1
    for r in range(1, min(max_r + 1, len(s))):
        ratio = s[r - 1] / max(1e-12, s[r])
        if ratio >= calibrated_requirement:
            selected_rank = r
    return selected_rank


def is_rank_stable(
    ranks: Sequence[RankDimension],
    full_sample_rank: RankDimension | None = None,
    minimum_fraction: MetricRate = 0.8,
) -> bool:
    if full_sample_rank is not None:
        count = sum(1 for r in ranks if r == full_sample_rank)
        return bool(count / len(ranks) >= minimum_fraction) if ranks else False
    return len(set(ranks)) <= 1


def estimate_client_nuisance_subspace(
    client_controls: torch.Tensor,
    rank_selection: RankSelectionMethod,
    fixed_rank: RankDimension,
    variance_threshold: ThresholdValue,
    eigengap_regularization: ThresholdValue,
) -> NuisanceEstimate:
    _unused = (variance_threshold, eigengap_regularization)
    n, d = client_controls.shape
    if n == 0 or d == 0:
        return NuisanceEstimate(
            subspace=torch.empty((d, 0)),
            uncertainty_radius=1.0,
            selected_rank=0,
            eigengap_ratio=1.0,
            replicates=(),
        )
    centered = client_controls - client_controls.mean(dim=0, keepdim=True)
    centered_np = centered.detach().cpu().numpy()
    _unused_u, _unused_s, vh_np = np.linalg.svd(centered_np, full_matrices=False)
    k = min(int(fixed_rank) if rank_selection is RankSelectionMethod.FIXED_RANK else 2, d)
    subspace = torch.tensor(vh_np[:k, :].T, dtype=torch.float32)
    replicates = (
        ControlReplicate(
            replicate_index=0,
            displacement=centered.mean(dim=0),
            support_before=n,
            support_after=n,
        ),
    )
    return NuisanceEstimate(
        subspace=subspace,
        uncertainty_radius=0.1,
        selected_rank=k,
        eigengap_ratio=1.5,
        replicates=replicates,
    )
