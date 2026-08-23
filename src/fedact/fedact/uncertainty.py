from __future__ import annotations

from typing import Annotated

import numpy as np
from numpy.typing import NDArray
from pydantic import Field

FloatArray = NDArray[np.float64]
Resamples = Annotated[int, Field(ge=1)]
Alpha = Annotated[float, Field(gt=0.0, le=0.5)]
UncertaintyTerm = Annotated[float, Field(ge=0.0)]
EigenFloor = Annotated[float, Field(gt=0.0)]


def sampling_uncertainty_quantile(
    bootstrap_norms: tuple[float, ...], alpha: Alpha
) -> UncertaintyTerm:
    if not bootstrap_norms:
        raise ValueError("sampling uncertainty requires bootstrap draws")
    return float(np.quantile(bootstrap_norms, 1.0 - alpha, method="linear"))


def subspace_uncertainty(
    perturbed_projectors: tuple[FloatArray, ...], reference: FloatArray, alpha: Alpha
) -> UncertaintyTerm:
    deviations = [
        float(np.linalg.norm(perturbed - reference, ord=2)) for perturbed in perturbed_projectors
    ]
    return float(np.quantile(deviations, 1.0 - alpha, method="linear"))


def standardized_subspace_term(
    subspace_deviation: UncertaintyTerm,
    amplitude: UncertaintyTerm,
    smallest_eigenvalue: EigenFloor,
) -> UncertaintyTerm:
    if smallest_eigenvalue <= 0.0:
        raise ValueError("standardization requires a positive minimal eigenvalue")
    return subspace_deviation * amplitude / float(np.sqrt(smallest_eigenvalue))


def client_radius(
    sampling: UncertaintyTerm,
    subspace: UncertaintyTerm,
    control_span: UncertaintyTerm,
    private_allowance: UncertaintyTerm,
) -> UncertaintyTerm:
    return sampling + subspace + control_span + private_allowance
