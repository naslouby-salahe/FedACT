from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

import numpy as np
import torch

from fedact.domain.types import (
    ClientIdentifier,
    EigengapRatio,
    RankDimension,
    SampleCount,
    ThresholdValue,
    ValidationFlag,
)


class ConstraintSummaryFailure(StrEnum):
    INSUFFICIENT_SUPPORT = "insufficient_support"
    CONTROL_DIAGNOSTICS_FAILED = "control_diagnostics_failed"


@dataclass(frozen=True)
class ClientConstraintSummary:
    support_before: SampleCount
    support_after: SampleCount
    eigengap_ratio: EigengapRatio
    subspace: torch.Tensor | None = None
    uncertainty_radius: ThresholdValue = 0.1
    beta: ThresholdValue = 1.0
    selected_rank: RankDimension = 1
    control_diagnostics_passed: ValidationFlag = True
    client_id: ClientIdentifier | None = None
    basis: np.ndarray | None = None
    transition_vector: np.ndarray | None = None
    covariance: np.ndarray | None = None


def validate_summary(
    summary: ClientConstraintSummary,
    minimum_support: SampleCount,
) -> ConstraintSummaryFailure | None:
    if summary.support_before < minimum_support or summary.support_after < minimum_support:
        return ConstraintSummaryFailure.INSUFFICIENT_SUPPORT
    if not summary.control_diagnostics_passed:
        return ConstraintSummaryFailure.CONTROL_DIAGNOSTICS_FAILED
    return None
