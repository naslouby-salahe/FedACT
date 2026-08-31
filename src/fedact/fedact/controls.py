from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch

from fedact.domain.records import (
    GateComplianceFlag,
    MetricRate,
    NormValue,
    ReplicateIndex,
    SampleCount,
    ThresholdValue,
)


@dataclass(frozen=True)
class ControlReplicate:
    replicate_index: ReplicateIndex
    displacement: torch.Tensor
    support_before: SampleCount
    support_after: SampleCount


@dataclass(frozen=True)
class ControlQualityGate:
    held_out_residual_quantile: ThresholdValue
    minimum_pass_fraction: MetricRate


def build_control_displacement(
    prior: np.ndarray | torch.Tensor,
    recent: np.ndarray | torch.Tensor,
) -> np.ndarray:
    p = prior.detach().cpu().numpy() if isinstance(prior, torch.Tensor) else prior
    r = recent.detach().cpu().numpy() if isinstance(recent, torch.Tensor) else recent
    return r - p


def held_out_reconstruction_residuals(
    replicates: Sequence[np.ndarray | torch.Tensor],
) -> tuple[NormValue, ...]:
    if not replicates:
        return ()
    arrs = [r.detach().cpu().numpy() if isinstance(r, torch.Tensor) else r for r in replicates]
    mean = np.mean(arrs, axis=0)
    return tuple(float(np.linalg.norm(r - mean)) for r in arrs)


def is_control_gate_passing(
    residuals: Sequence[NormValue],
    gate: ControlQualityGate,
) -> GateComplianceFlag:
    if not residuals:
        return False
    threshold = float(np.quantile(residuals, gate.held_out_residual_quantile))
    passed = sum(1 for r in residuals if r <= threshold)
    return bool(passed / len(residuals) >= gate.minimum_pass_fraction)


def filter_control_replicates(
    replicates: list[ControlReplicate],
    gate: ControlQualityGate,
) -> tuple[ControlReplicate, ...]:
    if not replicates:
        return ()
    residuals = held_out_reconstruction_residuals([r.displacement for r in replicates])
    threshold = float(np.quantile(residuals, gate.held_out_residual_quantile))
    return tuple(
        replicate
        for replicate, residual in zip(replicates, residuals, strict=True)
        if residual <= threshold
    )
