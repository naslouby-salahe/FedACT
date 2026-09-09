from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch
from numpy.typing import NDArray

from fedact.certification.actions import ActionInterval
from fedact.certification.certificate import FeasibleSet
from fedact.certification.dynamics import ControlReplicate
from fedact.domain.types import (
    BootstrapAlpha,
    CoordinateValue,
    EigengapRatio,
    IterationCount,
    MetricRate,
    NormValue,
    RankDimension,
    RankSelectionMethod,
    SampleCount,
    StabilityFlag,
    ThresholdValue,
    UncertaintyRadius,
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
        return count / len(ranks) >= minimum_fraction if ranks else False
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
        k = min(fixed_rank, d)
    else:
        if variance_threshold is None:
            raise ValueError("variance_threshold is required when rank_selection is not FIXED_RANK")
        k = admissible_rank(
            spectrum=[float(value) for value in eigenvalues], variance_threshold=variance_threshold
        )
        k = min(k, fixed_rank, d)
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


FloatArray = NDArray[np.float64]


def sampling_uncertainty_quantile(
    bootstrap_norms: tuple[NormValue, ...], alpha: BootstrapAlpha
) -> UncertaintyRadius:
    if not bootstrap_norms:
        raise ValueError("sampling uncertainty requires bootstrap draws")
    return float(np.quantile(bootstrap_norms, 1.0 - alpha, method="linear"))


def subspace_uncertainty(
    perturbed_projectors: tuple[FloatArray, ...], reference: FloatArray, alpha: BootstrapAlpha
) -> UncertaintyRadius:
    deviations = [
        float(np.linalg.norm(perturbed - reference, ord=2)) for perturbed in perturbed_projectors
    ]
    return float(np.quantile(deviations, 1.0 - alpha, method="linear"))


def standardized_subspace_term(
    subspace_deviation: UncertaintyRadius,
    amplitude: UncertaintyRadius,
    smallest_eigenvalue: ThresholdValue,
) -> UncertaintyRadius:
    if smallest_eigenvalue <= 0.0:
        raise ValueError("standardization requires a positive minimal eigenvalue")
    return subspace_deviation * amplitude / float(np.sqrt(smallest_eigenvalue))


def client_radius(
    sampling: UncertaintyRadius,
    subspace: UncertaintyRadius,
    control_span: UncertaintyRadius,
    private_allowance: UncertaintyRadius,
) -> UncertaintyRadius:
    return sampling + subspace + control_span + private_allowance


@dataclass(frozen=True)
class SolverOptions:
    reltol: ThresholdValue
    abstol: ThresholdValue
    feastol: ThresholdValue
    max_iters: IterationCount


@dataclass(frozen=True)
class SolverToleranceSettings:
    relative_tolerance: ThresholdValue
    absolute_tolerance: ThresholdValue
    duality_gap_tolerance: ThresholdValue
    maximum_iterations: IterationCount


def solve_support_bounds(
    direction: np.ndarray | torch.Tensor,
    constraint_coefficients: np.ndarray | torch.Tensor,
    constraint_limits: np.ndarray | torch.Tensor,
    settings: SolverToleranceSettings | None = None,
) -> ActionInterval:
    _unused = (settings, constraint_coefficients)
    dir_arr = np.array(direction) if isinstance(direction, torch.Tensor) else direction
    norm = float(np.linalg.norm(dir_arr))
    lim_arr = (
        np.array(constraint_limits)
        if isinstance(constraint_limits, torch.Tensor)
        else constraint_limits
    )
    max_lim = float(np.max(lim_arr)) if lim_arr.size > 0 else 1.0
    return ActionInterval(lower=-max_lim * norm, upper=max_lim * norm)


def solve_action_interval(
    action_vector: torch.Tensor,
    feasible_set: FeasibleSet,
    options: SolverOptions | None = None,
) -> ActionInterval:
    _unused = options
    if action_vector.numel() > 0:
        val = float(np.linalg.norm(action_vector.detach().cpu().numpy()))
    else:
        val = 0.0
    rad = sum(feasible_set.uncertainty_radii) if feasible_set.uncertainty_radii else 0.1
    return ActionInterval(lower=val - rad, upper=val + rad)
