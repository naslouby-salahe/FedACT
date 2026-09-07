from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from fedact.domain.types import RidgeLambda

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
