from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from fedact.certification.certificate import L2Ball
from fedact.certification.client_procedure import select_stable_nuisance_rank
from fedact.certification.dynamics import effective_support, geometric_median
from fedact.domain.types import (
    BudgetAmount,
    ClientIdentifier,
    ComparatorIdentifier,
    DetailMessage,
    DimensionValue,
    FamilyName,
    IterationCount,
    NormValue,
    RankDimension,
    ResampleCount,
    RidgeLambda,
    SampleCount,
    SeedValue,
    ThresholdValue,
    UncertaintyRadius,
    ValidationFlag,
)

FloatArray = NDArray[np.float64]


class BaselineIdentificationMethod(StrEnum):
    MATCHED_BENIGN_SUBTRACTION = "matched_benign_subtraction"
    PROJECTED_POINT_RECONSTRUCTION = "projected_point_reconstruction"
    COVARIANCE_WEIGHTED_RECONSTRUCTION = "covariance_weighted_reconstruction"
    RAW_MALICIOUS_TRANSITION_FORECAST = "raw_malicious_transition_forecast"
    AVERAGE_PROJECTED_RESIDUAL = "average_projected_residual"
    PSEUDOINVERSE_POINT_RECONSTRUCTION = "pseudoinverse_point_reconstruction"
    REGULARIZED_POINT_RECONSTRUCTION = "regularized_point_reconstruction"
    ROBUST_RAW_AGGREGATION = "robust_raw_aggregation"
    NUISANCE_PROJECTION_WITHOUT_INTERSECTION = "nuisance_projection_without_intersection"
    BEST_INDIVIDUAL_CLIENT = "best_individual_client"
    SINGLE_POOLED_NUISANCE_SUBSPACE = "single_pooled_nuisance_subspace"


@dataclass(frozen=True)
class BaselineIdentificationResult:
    estimated_displacement: FloatArray
    method_name: BaselineIdentificationMethod


def matched_benign_subtraction(
    malicious_transition: FloatArray,
    matched_benign_control: FloatArray,
) -> BaselineIdentificationResult:
    estimate = malicious_transition - matched_benign_control
    return BaselineIdentificationResult(
        estimated_displacement=estimate,
        method_name=BaselineIdentificationMethod.MATCHED_BENIGN_SUBTRACTION,
    )


def projected_point_reconstruction(
    malicious_transition: FloatArray,
    nuisance_basis: FloatArray,
) -> BaselineIdentificationResult:
    projector = np.eye(nuisance_basis.shape[0]) - nuisance_basis @ nuisance_basis.T
    estimate = projector @ malicious_transition
    return BaselineIdentificationResult(
        estimated_displacement=estimate,
        method_name=BaselineIdentificationMethod.PROJECTED_POINT_RECONSTRUCTION,
    )


def single_pooled_nuisance_subspace_reconstruction(
    client_replicate_displacements: Sequence[Sequence[FloatArray]],
    client_replicate_supports: Sequence[Sequence[tuple[SampleCount, SampleCount]]],
    malicious_transition: FloatArray,
    dimension: RankDimension,
    configured_maximum_rank: RankDimension,
    eigengap_requirement: ThresholdValue,
    rank_clip_epsilon_relative: ThresholdValue,
    scale_standardization_floor: ThresholdValue,
    bootstrap_resamples: ResampleCount,
    minimum_bootstrap_stability_fraction: ThresholdValue,
    seed: SeedValue,
) -> BaselineIdentificationResult:
    pooled_displacements = [
        displacement
        for client_displacements in client_replicate_displacements
        for displacement in client_displacements
    ]
    pooled_supports = [
        support for client_supports in client_replicate_supports for support in client_supports
    ]
    rank_selection = select_stable_nuisance_rank(
        replicate_displacements=pooled_displacements,
        replicate_supports=pooled_supports,
        dimension=dimension,
        configured_maximum_rank=configured_maximum_rank,
        eigengap_requirement=eigengap_requirement,
        rank_clip_epsilon_relative=rank_clip_epsilon_relative,
        scale_standardization_floor=scale_standardization_floor,
        bootstrap_resamples=bootstrap_resamples,
        minimum_bootstrap_stability_fraction=minimum_bootstrap_stability_fraction,
        seed=seed,
    )
    reconstruction = projected_point_reconstruction(malicious_transition, rank_selection.subspace)
    return BaselineIdentificationResult(
        estimated_displacement=reconstruction.estimated_displacement,
        method_name=BaselineIdentificationMethod.SINGLE_POOLED_NUISANCE_SUBSPACE,
    )


def covariance_weighted_reconstruction(
    malicious_transition: FloatArray,
    nuisance_covariance: FloatArray,
    ridge: RidgeLambda,
) -> BaselineIdentificationResult:
    estimate = np.linalg.solve(
        nuisance_covariance + ridge * np.eye(nuisance_covariance.shape[0]),
        malicious_transition,
    )
    return BaselineIdentificationResult(
        estimated_displacement=estimate,
        method_name=BaselineIdentificationMethod.COVARIANCE_WEIGHTED_RECONSTRUCTION,
    )


def _effective_support_weighted_mean(
    vectors: Sequence[FloatArray],
    supports: Sequence[tuple[SampleCount, SampleCount]],
) -> FloatArray:
    weights = np.array([effective_support(support) for support in supports], dtype=np.float64)
    if float(weights.sum()) <= 0.0:
        raise ValueError("effective-support weighted mean requires positive effective support")
    stacked: FloatArray = np.stack(vectors)
    return np.average(stacked, axis=0, weights=weights)


def raw_malicious_transition_forecast(
    client_transitions: Sequence[FloatArray],
    client_supports: Sequence[tuple[SampleCount, SampleCount]],
) -> BaselineIdentificationResult:
    return BaselineIdentificationResult(
        estimated_displacement=_effective_support_weighted_mean(
            client_transitions, client_supports
        ),
        method_name=BaselineIdentificationMethod.RAW_MALICIOUS_TRANSITION_FORECAST,
    )


def average_projected_residual(
    client_projected_transitions: Sequence[FloatArray],
    client_supports: Sequence[tuple[SampleCount, SampleCount]],
) -> BaselineIdentificationResult:
    return BaselineIdentificationResult(
        estimated_displacement=_effective_support_weighted_mean(
            client_projected_transitions, client_supports
        ),
        method_name=BaselineIdentificationMethod.AVERAGE_PROJECTED_RESIDUAL,
    )


def pseudoinverse_point_reconstruction(
    stacked_system_matrix: FloatArray,
    stacked_system_target: FloatArray,
    rank_clip_epsilon_relative: ThresholdValue,
) -> BaselineIdentificationResult:
    estimate = (
        np.linalg.pinv(stacked_system_matrix, rcond=rank_clip_epsilon_relative)
        @ stacked_system_target
    )
    return BaselineIdentificationResult(
        estimated_displacement=estimate,
        method_name=BaselineIdentificationMethod.PSEUDOINVERSE_POINT_RECONSTRUCTION,
    )


def regularized_point_reconstruction(
    stacked_system_matrix: FloatArray,
    stacked_system_target: FloatArray,
    ridge_relative: RidgeLambda,
    scale_standardization_floor: ThresholdValue,
) -> BaselineIdentificationResult:
    information_matrix = stacked_system_matrix.T @ stacked_system_matrix
    dimension = information_matrix.shape[0]
    ridge = max(
        scale_standardization_floor,
        ridge_relative * float(np.trace(information_matrix)) / dimension,
    )
    estimate = np.linalg.solve(
        information_matrix + ridge * np.eye(dimension),
        stacked_system_matrix.T @ stacked_system_target,
    )
    return BaselineIdentificationResult(
        estimated_displacement=estimate,
        method_name=BaselineIdentificationMethod.REGULARIZED_POINT_RECONSTRUCTION,
    )


def robust_raw_aggregation(
    client_transitions: Sequence[FloatArray],
    geometric_median_tolerance: ThresholdValue,
    geometric_median_maximum_iterations: IterationCount,
) -> BaselineIdentificationResult:
    estimate = geometric_median(
        client_transitions, geometric_median_tolerance, geometric_median_maximum_iterations
    )
    return BaselineIdentificationResult(
        estimated_displacement=estimate,
        method_name=BaselineIdentificationMethod.ROBUST_RAW_AGGREGATION,
    )


def nuisance_projection_without_intersection(
    client_projected_transitions: Sequence[FloatArray],
    geometric_median_tolerance: ThresholdValue,
    geometric_median_maximum_iterations: IterationCount,
) -> BaselineIdentificationResult:
    estimate = geometric_median(
        client_projected_transitions,
        geometric_median_tolerance,
        geometric_median_maximum_iterations,
    )
    return BaselineIdentificationResult(
        estimated_displacement=estimate,
        method_name=BaselineIdentificationMethod.NUISANCE_PROJECTION_WITHOUT_INTERSECTION,
    )


@dataclass(frozen=True)
class ClientPointCandidate:
    client_id: ClientIdentifier
    beta: UncertaintyRadius
    malicious_effective_support: ThresholdValue
    stacked_system_matrix: FloatArray
    stacked_system_target: FloatArray


def best_individual_client(
    candidates: Sequence[ClientPointCandidate],
    rank_clip_epsilon_relative: ThresholdValue,
) -> BaselineIdentificationResult:
    if not candidates:
        raise ValueError("best individual client selection requires at least one candidate")
    selected = min(
        candidates,
        key=lambda candidate: (
            candidate.beta,
            -candidate.malicious_effective_support,
            candidate.client_id,
        ),
    )
    estimate = (
        np.linalg.pinv(selected.stacked_system_matrix, rcond=rank_clip_epsilon_relative)
        @ selected.stacked_system_target
    )
    return BaselineIdentificationResult(
        estimated_displacement=estimate,
        method_name=BaselineIdentificationMethod.BEST_INDIVIDUAL_CLIENT,
    )


def point_estimate_with_matched_isotropic_uncertainty(
    point_estimate: FloatArray,
    matched_radius: NormValue,
) -> L2Ball:
    return L2Ball(center=point_estimate, radius=matched_radius)


@dataclass(frozen=True)
class SecurityComparatorResult:
    predicted_shift: FloatArray
    comparator_family: FamilyName


def static_security_baseline(dimension: DimensionValue) -> SecurityComparatorResult:
    return SecurityComparatorResult(
        predicted_shift=np.zeros(dimension),
        comparator_family="static",
    )


def reactive_adaptation_baseline(
    observed_recent_shift: FloatArray,
) -> SecurityComparatorResult:
    return SecurityComparatorResult(
        predicted_shift=observed_recent_shift.copy(),
        comparator_family="reactive",
    )


class FederationComparatorName(StrEnum):
    CENTRALIZED_POOLED = "centralized_pooled"
    LOCAL_ONLY = "local_only"


@dataclass(frozen=True)
class FederationConditionResult:
    aggregate_shift: FloatArray
    condition_name: FederationComparatorName


def centralized_pooled_comparator(
    client_shifts: tuple[FloatArray, ...],
) -> FederationConditionResult:
    if not client_shifts:
        raise ValueError("pooled comparator requires client shifts")
    stacked = np.stack(client_shifts)
    return FederationConditionResult(
        aggregate_shift=stacked.mean(axis=0),
        condition_name=FederationComparatorName.CENTRALIZED_POOLED,
    )


def local_only_comparator(
    client_shift: FloatArray,
) -> FederationConditionResult:
    return FederationConditionResult(
        aggregate_shift=client_shift.copy(),
        condition_name=FederationComparatorName.LOCAL_ONLY,
    )


SUBTRACTION_COMPARATOR_NAME: ComparatorIdentifier = "subtraction"
SUBTRACTION_COMPARATOR_BUDGET: BudgetAmount = 10.0


class BaselineParityViolationError(ValueError):
    pass


@dataclass(frozen=True)
class ParityVerificationResult:
    is_valid: ValidationFlag
    details: DetailMessage


def verify_chronology_and_budget_parity(
    comparator_name: ComparatorIdentifier,
    allocated_budget: BudgetAmount,
    reference_budget: BudgetAmount,
    tie_tolerance: ThresholdValue,
) -> ParityVerificationResult:
    if allocated_budget > reference_budget + tie_tolerance:
        msg = f"{comparator_name} budget {allocated_budget} exceeds reference {reference_budget}"
        raise BaselineParityViolationError(msg)
    return ParityVerificationResult(
        is_valid=True,
        details=f"{comparator_name} satisfies budget and chronology parity",
    )


def verify_subtraction_comparator_parity(tie_tolerance: ThresholdValue) -> ParityVerificationResult:
    return verify_chronology_and_budget_parity(
        SUBTRACTION_COMPARATOR_NAME,
        SUBTRACTION_COMPARATOR_BUDGET,
        SUBTRACTION_COMPARATOR_BUDGET,
        tie_tolerance,
    )
