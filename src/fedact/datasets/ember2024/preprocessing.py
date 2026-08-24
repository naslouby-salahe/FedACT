from __future__ import annotations

import numpy as np


def apply_log1p_transforms(features: np.ndarray) -> np.ndarray:
    return np.log1p(np.maximum(features, 0.0))


def standardize_ember_features(features: np.ndarray) -> np.ndarray:
    if features.shape[0] == 0:
        return features
    mean = np.mean(features, axis=0)
    std = np.std(features, axis=0)
    std[std < 1e-12] = 1.0
    return (features - mean) / std
