from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from fedact.core.transitions import ClientIdentifier
from fedact.domain.records import (
    EigengapRatio,
    RankDimension,
    SampleCount,
    ThresholdValue,
    WorkflowStatus,
)


@dataclass(frozen=True)
class ClientConstraintSummary:
    support_before: SampleCount
    support_after: SampleCount
    eigengap_ratio: EigengapRatio
    subspace: torch.Tensor | None = None
    uncertainty_radius: ThresholdValue = 0.1
    beta: ThresholdValue = 1.0
    selected_rank: RankDimension = 1
    control_diagnostics_passed: bool = True
    client_id: ClientIdentifier | None = None
    basis: np.ndarray | None = None
    transition_vector: np.ndarray | None = None
    covariance: np.ndarray | None = None


def validate_summary(
    summary: ClientConstraintSummary,
    minimum_support: SampleCount,
) -> WorkflowStatus | None:
    if summary.support_before < minimum_support or summary.support_after < minimum_support:
        return "insufficient_support"
    if not summary.control_diagnostics_passed:
        return "control_diagnostics_failed"
    return None
