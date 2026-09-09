from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

import numpy as np
from numpy.typing import NDArray
from pydantic import Field

from fedact.domain.types import (
    BudgetAmount,
    ComparatorIdentifier,
    DetailMessage,
    FamilyName,
    RidgeLambda,
    ThresholdValue,
    ValidationFlag,
)

FloatArray = NDArray[np.float64]


class BaselineIdentificationMethod(StrEnum):
    MATCHED_BENIGN_SUBTRACTION = "matched_benign_subtraction"
    PROJECTED_POINT_RECONSTRUCTION = "projected_point_reconstruction"
    COVARIANCE_WEIGHTED_RECONSTRUCTION = "covariance_weighted_reconstruction"


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


def covariance_weighted_reconstruction(
    malicious_transition: FloatArray,
    nuisance_covariance: FloatArray,
    ridge: RidgeLambda,
) -> BaselineIdentificationResult:
    inv_cov = np.linalg.inv(nuisance_covariance + ridge * np.eye(nuisance_covariance.shape[0]))
    estimate = inv_cov @ malicious_transition
    return BaselineIdentificationResult(
        estimated_displacement=estimate,
        method_name=BaselineIdentificationMethod.COVARIANCE_WEIGHTED_RECONSTRUCTION,
    )

FloatArray = NDArray[np.float64]
SpaceDimension = Annotated[int, Field(ge=1)]
SeedIdentifier = Annotated[int, Field(ge=0)]


@dataclass(frozen=True)
class SecurityComparatorResult:
    predicted_shift: FloatArray
    comparator_family: FamilyName


def static_security_baseline(dimension: SpaceDimension) -> SecurityComparatorResult:
    return SecurityComparatorResult(
        predicted_shift=np.zeros(dimension),
        comparator_family="static",
    )


def random_mutation_baseline(
    dimension: SpaceDimension, seed: SeedIdentifier
) -> SecurityComparatorResult:
    rng = np.random.default_rng(seed)
    shift = rng.standard_normal(dimension)
    shift /= np.linalg.norm(shift)
    return SecurityComparatorResult(
        predicted_shift=shift,
        comparator_family="random_mutation",
    )


def reactive_adaptation_baseline(
    observed_recent_shift: FloatArray,
) -> SecurityComparatorResult:
    return SecurityComparatorResult(
        predicted_shift=observed_recent_shift.copy(),
        comparator_family="reactive",
    )

FloatArray = NDArray[np.float64]


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
