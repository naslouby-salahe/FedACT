from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import numpy as np
from numpy.typing import NDArray
from pydantic import Field

from fedact.fedact.transitions import AbstentionReason, ClientIdentifier

FloatArray = NDArray[np.float64]


SupportFloor = Annotated[int, Field(ge=1)]


@dataclass(frozen=True)
class ClientConstraintSummary:
    client_id: ClientIdentifier
    basis: FloatArray
    transition_vector: FloatArray
    covariance: FloatArray
    support_before: int
    support_after: int
    beta: float
    eigengap_ratio: float
    selected_rank: int
    control_diagnostics_passed: bool


def validate_summary(
    summary: ClientConstraintSummary, minimum_support: SupportFloor
) -> AbstentionReason | None:
    if summary.support_before < minimum_support or summary.support_after < minimum_support:
        return AbstentionReason.ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT
    if not np.all(np.isfinite(summary.covariance)):
        raise ValueError("client covariance must be finite before transmission")
    if summary.beta <= 0.0 or not np.isfinite(summary.beta):
        return AbstentionReason.ABSTAIN_FEASIBLE_SET_INCONSISTENT
    if not summary.control_diagnostics_passed:
        return AbstentionReason.ABSTAIN_CONTROL_RECONSTRUCTION_FAILURE
    eigenvalues = np.linalg.eigvalsh(summary.covariance)
    if float(eigenvalues.min()) <= 0.0:
        raise ValueError("client covariance must be positive definite at transmission")
    return None
