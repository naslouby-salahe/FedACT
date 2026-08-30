from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch

from fedact.domain.types import IntervalBound, NormValue, ThresholdValue, ValidationFlag
from fedact.fedact.estimand import ActionInterval


@dataclass(frozen=True)
class ActionDisplacementResult:
    displacement_vector: torch.Tensor | np.ndarray
    displacement_norm: NormValue
    rejected_as_degenerate: ValidationFlag


def evaluate_displacement(
    source: np.ndarray | torch.Tensor,
    target: np.ndarray | torch.Tensor,
    zero_displacement_floor: ThresholdValue,
) -> ActionDisplacementResult:
    s = np.array(source) if isinstance(source, torch.Tensor) else source
    t = np.array(target) if isinstance(target, torch.Tensor) else target
    delta = t - s
    norm = float(np.linalg.norm(delta))
    degen = norm < zero_displacement_floor
    return ActionDisplacementResult(
        displacement_vector=delta,
        displacement_norm=norm,
        rejected_as_degenerate=degen,
    )


def action_support_bounds(
    direction: np.ndarray | torch.Tensor,
    vertices: Sequence[np.ndarray | torch.Tensor],
) -> ActionInterval:
    d = np.array(direction) if isinstance(direction, torch.Tensor) else direction
    values = [float(np.dot(d, np.array(v) if isinstance(v, torch.Tensor) else v)) for v in vertices]
    return ActionInterval(lower=min(values), upper=max(values))


def box_diameter_bound(
    lowers: Sequence[IntervalBound],
    uppers: Sequence[IntervalBound],
) -> IntervalBound:
    diffs = [u_val - l_val for l_val, u_val in zip(lowers, uppers, strict=True)]
    return float(np.sqrt(sum(d * d for d in diffs)))


def displace_sample_representation(
    source_representation: torch.Tensor,
    action_delta: torch.Tensor,
    norm_floor: NormValue,
) -> ActionDisplacementResult:
    norm = float(np.linalg.norm(action_delta.detach().cpu().numpy()))
    degen = norm < norm_floor
    res = source_representation + action_delta if not degen else source_representation
    return ActionDisplacementResult(
        displacement_vector=res,
        displacement_norm=norm,
        rejected_as_degenerate=degen,
    )
