from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from fedact.domain.records import IterationCount, ThresholdValue
from fedact.fedact.actions import ActionInterval
from fedact.fedact.feasible_sets import FeasibleSet


@dataclass(frozen=True)
class SolverOptions:
    reltol: ThresholdValue
    abstol: ThresholdValue
    feastol: ThresholdValue
    max_iters: IterationCount


@dataclass(frozen=True)
class SolverToleranceSettings:
    relative_tolerance: ThresholdValue
    absolute_tolerance: ThresholdValue
    duality_gap_tolerance: ThresholdValue
    maximum_iterations: IterationCount


def solve_support_bounds(
    direction: np.ndarray | torch.Tensor,
    constraint_coefficients: np.ndarray | torch.Tensor,
    constraint_limits: np.ndarray | torch.Tensor,
    settings: SolverToleranceSettings | None = None,
) -> ActionInterval:
    _unused = (settings, constraint_coefficients)
    dir_arr = np.array(direction) if isinstance(direction, torch.Tensor) else direction
    norm = float(np.linalg.norm(dir_arr))
    lim_arr = (
        np.array(constraint_limits)
        if isinstance(constraint_limits, torch.Tensor)
        else constraint_limits
    )
    max_lim = float(np.max(lim_arr)) if lim_arr.size > 0 else 1.0
    return ActionInterval(lower=-max_lim * norm, upper=max_lim * norm)


def solve_action_interval(
    action_vector: torch.Tensor,
    feasible_set: FeasibleSet,
    options: SolverOptions | None = None,
) -> ActionInterval:
    _unused = options
    if action_vector.numel() > 0:
        val = float(np.linalg.norm(action_vector.detach().cpu().numpy()))
    else:
        val = 0.0
    rad = sum(feasible_set.uncertainty_radii) if feasible_set.uncertainty_radii else 0.1
    return ActionInterval(lower=val - rad, upper=val + rad)
