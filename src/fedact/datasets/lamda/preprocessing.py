from __future__ import annotations

from typing import Annotated

import numpy as np
from pydantic import Field

VarianceBound = Annotated[float, Field(ge=0.0)]


def filter_low_variance_features(
    features: np.ndarray, variance_threshold: VarianceBound = 1e-4
) -> np.ndarray:
    if features.shape[0] == 0:
        return features
    variances = np.var(features, axis=0)
    keep = variances >= variance_threshold
    if not np.any(keep):
        return features
    return features[:, keep]


def standardize_features(features: np.ndarray) -> np.ndarray:
    if features.shape[0] == 0:
        return features
    mean = np.mean(features, axis=0)
    std = np.std(features, axis=0)
    std[std == 0.0] = 1.0
    return (features - mean) / std
