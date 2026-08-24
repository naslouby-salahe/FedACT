from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch

from fedact.domain.types import CoordinateValue, NormValue, SampleCount, ThresholdValue


@dataclass(frozen=True)
class TemporalModel:
    scalar_coefficient: ThresholdValue
    process_error_radius: NormValue
    consecutive_pairs_used: SampleCount


def fit_scalar_model(
    centers: Sequence[np.ndarray | torch.Tensor],
    maximum_coefficient: ThresholdValue = 0.99,
) -> tuple[float, np.ndarray]:
    if len(centers) < 2:
        return 1.0, np.zeros((1, 1))
    arrs = [np.array(c) if isinstance(c, torch.Tensor) else c for c in centers]
    x = np.stack(arrs[:-1])
    y = np.stack(arrs[1:])
    denom = np.sum(x * x)
    a = float(np.sum(x * y) / denom) if denom > 1e-12 else 1.0
    a = min(maximum_coefficient, max(-maximum_coefficient, a))
    residuals = y - a * x
    return a, residuals


def process_error_radius(
    residuals: np.ndarray | torch.Tensor,
    quantile: ThresholdValue = 0.9,
) -> NormValue:
    arr = np.array(residuals) if isinstance(residuals, torch.Tensor) else residuals
    norms = np.linalg.norm(arr, axis=-1)
    return float(np.quantile(norms, quantile)) if norms.size > 0 else 0.1


def propagate_radius(
    initial_radius: NormValue | None = None,
    a_coefficient: CoordinateValue | None = None,
    process_noise_radius: NormValue | None = None,
    horizon_steps: SampleCount = 1,
    initial_set_radius: NormValue | None = None,
    coefficient: CoordinateValue | None = None,
    process_radius: NormValue | None = None,
) -> NormValue:
    if initial_radius is not None:
        r0 = initial_radius
    elif initial_set_radius is not None:
        r0 = initial_set_radius
    else:
        r0 = 1.0

    if a_coefficient is not None:
        a = a_coefficient
    elif coefficient is not None:
        a = coefficient
    else:
        a = 1.0

    if process_noise_radius is not None:
        rw = process_noise_radius
    elif process_radius is not None:
        rw = process_radius
    else:
        rw = 0.1

    r = r0
    for _ in range(horizon_steps):
        r = abs(a) * r + rw
    return float(r)


def fit_scalar_ar1(historical_centers: Sequence[torch.Tensor]) -> TemporalModel:
    if len(historical_centers) < 2:
        return TemporalModel(
            scalar_coefficient=1.0, process_error_radius=0.1, consecutive_pairs_used=0
        )
    x = torch.stack(list(historical_centers[:-1]))
    y = torch.stack(list(historical_centers[1:]))
    a = float(((x * y).sum() / (x * x).sum().clamp_min(1e-12)).detach().cpu().item())
    diff_np = (y - a * x).detach().cpu().numpy()
    err = float(np.max(np.linalg.norm(diff_np, axis=-1)))
    return TemporalModel(
        scalar_coefficient=a,
        process_error_radius=err,
        consecutive_pairs_used=len(historical_centers) - 1,
    )
