from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch

from fedact.core.controls import ControlReplicate
from fedact.domain.enums import RankSelectionMethod
from fedact.domain.records import (
    CoordinateValue,
    EigengapRatio,
    MetricRate,
    RankDimension,
    SampleCount,
    StabilityFlag,
    ThresholdValue,
)

_PLACEHOLDER_UNCERTAINTY_RADIUS = 0.1


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
    coefficient: CoordinateValue,
    floor: CoordinateValue,
    regularization: ThresholdValue | None = None,
) -> np.ndarray:
    reg = max(regularization if regularization is not None else coefficient, floor)
    c = np.array(covariance) if isinstance(covariance, torch.Tensor) else covariance
    return c + reg * np.eye(c.shape[0])


def admissible_rank(
    spectrum: Sequence[CoordinateValue] | None = None,
    variance_threshold: ThresholdValue | None = None,
    dimension: RankDimension | None = None,
    replicates: SampleCount | None = None,
    configured_maximum: RankDimension | None = None,
) -> RankDimension:
    if dimension is not None and replicates is not None and configured_maximum is not None:
        return min(dimension - 1, replicates - 1, configured_maximum)
    if spectrum is not None and variance_threshold is not None:
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
    clip_relative: ThresholdValue,
    floor: ThresholdValue,
) -> EigengapRatio:
    s = sorted(spectrum, reverse=True)
    if rank <= 0 or rank >= len(s):
        return 1.0
    denominator = max(s[rank], clip_relative * s[0], floor)
    return float(s[rank - 1] / denominator)


def select_rank_by_eigengap(
    spectrum: Sequence[CoordinateValue] | np.ndarray,
    calibrated_requirement: ThresholdValue,
    clip_relative: ThresholdValue,
    floor: ThresholdValue,
    maximum_rank: RankDimension | None = None,
    maximum_admissible: RankDimension | None = None,
) -> RankDimension:
    s = sorted(spectrum, reverse=True)
    if maximum_admissible is not None:
        max_r = maximum_admissible
    elif maximum_rank is not None:
        max_r = maximum_rank
    else:
        max_r = len(s) - 1

    selected_rank = 1
    for r in range(1, min(max_r + 1, len(s))):
        ratio = eigengap_ratio(s, rank=r, clip_relative=clip_relative, floor=floor)
        if ratio >= calibrated_requirement:
            selected_rank = r
    return selected_rank


def is_rank_stable(
    ranks: Sequence[RankDimension],
    minimum_fraction: MetricRate,
    full_sample_rank: RankDimension | None = None,
) -> StabilityFlag:
    if full_sample_rank is not None:
        count = sum(1 for r in ranks if r == full_sample_rank)
        return bool(count / len(ranks) >= minimum_fraction) if ranks else False
    return len(set(ranks)) <= 1


def estimate_client_nuisance_subspace(
    client_controls: torch.Tensor,
    rank_selection: RankSelectionMethod,
    fixed_rank: RankDimension,
    eigengap_regularization: ThresholdValue,
    scale_standardization_floor: ThresholdValue,
    variance_threshold: ThresholdValue | None = None,
) -> NuisanceEstimate:
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
    covariance_raw = weighted_covariance(centered_np)
    covariance = regularized_covariance(
        covariance_raw, coefficient=eigengap_regularization, floor=scale_standardization_floor
    )
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]

    if rank_selection is RankSelectionMethod.FIXED_RANK:
        k = min(int(fixed_rank), d)
    else:
        if variance_threshold is None:
            raise ValueError("variance_threshold is required when rank_selection is not FIXED_RANK")
        k = admissible_rank(
            spectrum=[float(value) for value in eigenvalues], variance_threshold=variance_threshold
        )
        k = min(k, int(fixed_rank), d)
    k = max(1, k)
    subspace = torch.tensor(eigenvectors[:, :k], dtype=torch.float32)
    ratio = eigengap_ratio(
        eigenvalues,
        rank=k,
        clip_relative=eigengap_regularization,
        floor=scale_standardization_floor,
    )
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
        uncertainty_radius=_PLACEHOLDER_UNCERTAINTY_RADIUS,
        selected_rank=k,
        eigengap_ratio=ratio,
        replicates=replicates,
    )
