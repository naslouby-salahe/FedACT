from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch
from numpy.typing import NDArray

from fedact.certification.actions import projector_from_basis
from fedact.certification.dynamics import (
    ControlReplicate,
    effective_support,
    geometric_median,
    observed_nuisance_amplitude,
)
from fedact.certification.uncertainty import (
    admissible_rank,
    eigengap_ratio,
    is_rank_stable,
    sampling_uncertainty_quantile,
    select_rank_by_eigengap,
    standardized_subspace_term,
    subspace_uncertainty,
    weighted_covariance,
)
from fedact.domain.types import (
    BootstrapAlpha,
    EigengapRatio,
    IterationCount,
    NormValue,
    RankDimension,
    ResampleCount,
    SampleCount,
    SeedValue,
    StabilityFlag,
    ThresholdValue,
    UncertaintyRadius,
)

FloatArray = NDArray[np.float64]
_NUISANCE_AMPLITUDE_BOUND_PERCENTILE = 0.95


def mahalanobis_norm(vector: FloatArray, covariance: FloatArray) -> NormValue:
    solved = np.linalg.solve(covariance, vector)
    return float(np.sqrt(max(float(vector @ solved), 0.0)))


def malicious_transition_covariance(
    window_minus: FloatArray, window_plus: FloatArray
) -> FloatArray:
    dimension = window_minus.shape[1]
    covariance_minus = (
        np.cov(window_minus, rowvar=False) if window_minus.shape[0] > 1 else np.eye(dimension)
    )
    covariance_plus = (
        np.cov(window_plus, rowvar=False) if window_plus.shape[0] > 1 else np.eye(dimension)
    )
    return covariance_minus / window_minus.shape[0] + covariance_plus / window_plus.shape[0]


@dataclass(frozen=True)
class NuisanceRankSelectionResult:
    covariance_raw: FloatArray
    selected_rank: RankDimension
    eigengap_ratio: EigengapRatio
    subspace: FloatArray
    is_stable: StabilityFlag


def select_stable_nuisance_rank(
    replicate_displacements: Sequence[FloatArray],
    replicate_supports: Sequence[tuple[SampleCount, SampleCount]],
    dimension: RankDimension,
    configured_maximum_rank: RankDimension,
    eigengap_requirement: ThresholdValue,
    rank_clip_epsilon_relative: ThresholdValue,
    scale_standardization_floor: ThresholdValue,
    bootstrap_resamples: ResampleCount,
    minimum_bootstrap_stability_fraction: ThresholdValue,
    seed: SeedValue,
) -> NuisanceRankSelectionResult:
    weights = [effective_support(support) for support in replicate_supports]
    covariance_raw = weighted_covariance(list(replicate_displacements), weights)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance_raw)
    order = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[order]
    eigenvectors = eigenvectors[:, order]
    r_max_data = admissible_rank(
        dimension=dimension,
        replicates=len(replicate_displacements),
        configured_maximum=configured_maximum_rank,
    )
    selected_rank = select_rank_by_eigengap(
        eigenvalues,
        maximum_admissible=r_max_data,
        calibrated_requirement=eigengap_requirement,
        clip_relative=rank_clip_epsilon_relative,
        floor=scale_standardization_floor,
    )
    ratio = eigengap_ratio(
        eigenvalues,
        rank=selected_rank,
        clip_relative=rank_clip_epsilon_relative,
        floor=scale_standardization_floor,
    )
    rng = np.random.default_rng(seed)
    replicate_count = len(replicate_displacements)
    bootstrap_ranks: list[RankDimension] = []
    for _draw in range(bootstrap_resamples):
        draw_indices: list[int] = rng.integers(0, replicate_count, size=replicate_count).tolist()
        draw_displacements = [replicate_displacements[index] for index in draw_indices]
        draw_weights = [weights[index] for index in draw_indices]
        draw_covariance = weighted_covariance(draw_displacements, draw_weights)
        draw_eigenvalues = np.sort(np.linalg.eigvalsh(draw_covariance))[::-1]
        draw_r_max = admissible_rank(
            dimension=dimension,
            replicates=replicate_count,
            configured_maximum=configured_maximum_rank,
        )
        bootstrap_ranks.append(
            select_rank_by_eigengap(
                draw_eigenvalues,
                maximum_admissible=draw_r_max,
                calibrated_requirement=eigengap_requirement,
                clip_relative=rank_clip_epsilon_relative,
                floor=scale_standardization_floor,
            )
        )
    stable = is_rank_stable(
        bootstrap_ranks,
        minimum_fraction=minimum_bootstrap_stability_fraction,
        full_sample_rank=selected_rank,
    )
    subspace = eigenvectors[:, :selected_rank]
    return NuisanceRankSelectionResult(
        covariance_raw=covariance_raw,
        selected_rank=selected_rank,
        eigengap_ratio=ratio,
        subspace=subspace,
        is_stable=stable,
    )


def bootstrap_malicious_sampling_term(
    window_minus: FloatArray,
    window_plus: FloatArray,
    observed_transition: FloatArray,
    projector: FloatArray,
    malicious_covariance: FloatArray,
    alpha: BootstrapAlpha,
    resamples: ResampleCount,
    seed: SeedValue,
) -> UncertaintyRadius:
    rng = np.random.default_rng(seed)
    n_minus = window_minus.shape[0]
    n_plus = window_plus.shape[0]
    norms: list[NormValue] = []
    for _draw in range(resamples):
        draw_minus = window_minus[rng.integers(0, n_minus, size=n_minus)]
        draw_plus = window_plus[rng.integers(0, n_plus, size=n_plus)]
        draw_transition = draw_plus.mean(axis=0) - draw_minus.mean(axis=0)
        residual = projector @ (draw_transition - observed_transition)
        norms.append(mahalanobis_norm(residual, malicious_covariance))
    return sampling_uncertainty_quantile(tuple(norms), alpha)


def bootstrap_subspace_estimation_term(
    replicate_displacements: Sequence[FloatArray],
    replicate_supports: Sequence[tuple[SampleCount, SampleCount]],
    selected_rank: RankDimension,
    reference_projector: FloatArray,
    alpha: BootstrapAlpha,
    resamples: ResampleCount,
    seed: SeedValue,
    smallest_malicious_eigenvalue: ThresholdValue,
) -> UncertaintyRadius:
    weights = [effective_support(support) for support in replicate_supports]
    amplitude = observed_nuisance_amplitude(
        replicate_displacements,
        quantile=_NUISANCE_AMPLITUDE_BOUND_PERCENTILE,
        supports=replicate_supports,
    )
    rng = np.random.default_rng(seed)
    replicate_count = len(replicate_displacements)
    perturbed_projectors: list[FloatArray] = []
    for _draw in range(resamples):
        draw_indices: list[int] = rng.integers(0, replicate_count, size=replicate_count).tolist()
        draw_displacements = [replicate_displacements[index] for index in draw_indices]
        draw_weights = [weights[index] for index in draw_indices]
        draw_covariance = weighted_covariance(draw_displacements, draw_weights)
        draw_eigenvalues, draw_eigenvectors = np.linalg.eigh(draw_covariance)
        draw_order = np.argsort(draw_eigenvalues)[::-1]
        draw_subspace = draw_eigenvectors[:, draw_order][:, :selected_rank]
        perturbed_projectors.append(projector_from_basis(draw_subspace))
    subspace_deviation = subspace_uncertainty(
        tuple(perturbed_projectors), reference_projector, alpha
    )
    return standardized_subspace_term(subspace_deviation, amplitude, smallest_malicious_eigenvalue)


def control_span_violation_term(
    replicate_displacements: Sequence[FloatArray],
    replicate_supports: Sequence[tuple[SampleCount, SampleCount]],
    selected_rank: RankDimension,
    alpha: BootstrapAlpha,
    smallest_malicious_eigenvalue: ThresholdValue,
) -> UncertaintyRadius:
    weights = [effective_support(support) for support in replicate_supports]
    residuals: list[NormValue] = []
    for held_out in range(len(replicate_displacements)):
        remaining_displacements = [
            displacement
            for index, displacement in enumerate(replicate_displacements)
            if index != held_out
        ]
        remaining_weights = [weight for index, weight in enumerate(weights) if index != held_out]
        remaining_covariance = weighted_covariance(remaining_displacements, remaining_weights)
        remaining_eigenvalues, remaining_eigenvectors = np.linalg.eigh(remaining_covariance)
        remaining_order = np.argsort(remaining_eigenvalues)[::-1]
        remaining_subspace = remaining_eigenvectors[:, remaining_order][:, :selected_rank]
        remaining_projector = projector_from_basis(remaining_subspace)
        remaining_center = np.average(
            np.stack(remaining_displacements), axis=0, weights=remaining_weights
        )
        residual = remaining_projector @ (replicate_displacements[held_out] - remaining_center)
        residuals.append(float(np.linalg.norm(residual)))
    quantile_residual = sampling_uncertainty_quantile(tuple(residuals), alpha)
    return quantile_residual / np.sqrt(max(smallest_malicious_eigenvalue, 1e-12))


def private_transition_term_single_client(
    other_earlier_transitions: Sequence[FloatArray],
    projector: FloatArray,
    alpha: BootstrapAlpha,
    smallest_malicious_eigenvalue: ThresholdValue,
    geometric_median_tolerance: ThresholdValue,
    geometric_median_maximum_iterations: IterationCount,
) -> UncertaintyRadius | None:
    if len(other_earlier_transitions) < 2:
        return None
    projected = [projector @ transition for transition in other_earlier_transitions]
    residuals: list[NormValue] = []
    for held_out in range(len(projected)):
        remaining = [value for index, value in enumerate(projected) if index != held_out]
        median = geometric_median(
            remaining, geometric_median_tolerance, geometric_median_maximum_iterations
        )
        residuals.append(float(np.linalg.norm(projected[held_out] - median)))
    quantile_residual = sampling_uncertainty_quantile(tuple(residuals), alpha)
    return quantile_residual / np.sqrt(max(smallest_malicious_eigenvalue, 1e-12))


def as_float_array(tensor: torch.Tensor | FloatArray) -> FloatArray:
    if isinstance(tensor, torch.Tensor):
        return tensor.detach().cpu().numpy().astype(np.float64)
    return np.asarray(tensor, dtype=np.float64)


def replicate_supports_from(
    replicates: Sequence[ControlReplicate],
) -> tuple[tuple[SampleCount, SampleCount], ...]:
    return tuple((replicate.support_before, replicate.support_after) for replicate in replicates)
