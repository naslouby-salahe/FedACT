from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import numpy as np
from numpy.typing import NDArray
from pydantic import Field

FloatArray = NDArray[np.float64]
RidgeLambda = Annotated[float, Field(ge=0.0)]


@dataclass(frozen=True)
class BaselineIdentificationResult:
    estimated_displacement: FloatArray
    method_name: str


def matched_benign_subtraction(
    malicious_transition: FloatArray,
    matched_benign_control: FloatArray,
) -> BaselineIdentificationResult:
    estimate = malicious_transition - matched_benign_control
    return BaselineIdentificationResult(
        estimated_displacement=estimate,
        method_name="matched_benign_subtraction",
    )


def projected_point_reconstruction(
    malicious_transition: FloatArray,
    nuisance_basis: FloatArray,
) -> BaselineIdentificationResult:
    projector = np.eye(nuisance_basis.shape[0]) - nuisance_basis @ nuisance_basis.T
    estimate = projector @ malicious_transition
    return BaselineIdentificationResult(
        estimated_displacement=estimate,
        method_name="projected_point_reconstruction",
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
        method_name="covariance_weighted_reconstruction",
    )
