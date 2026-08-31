from __future__ import annotations

import numpy as np

from fedact.core.constraints import ClientConstraintSummary, validate_summary
from fedact.core.transitions import ClientIdentifier


def test_validate_summary_accepts_valid_data() -> None:
    summary = ClientConstraintSummary(
        client_id=ClientIdentifier("client-1"),
        basis=np.eye(4)[:, :2],
        transition_vector=np.ones(4),
        covariance=np.eye(4),
        support_before=10,
        support_after=10,
        beta=1.2,
        eigengap_ratio=2.0,
        selected_rank=2,
        control_diagnostics_passed=True,
    )
    assert validate_summary(summary, minimum_support=5) is None


def test_validate_summary_rejects_insufficient_support() -> None:
    summary = ClientConstraintSummary(
        client_id=ClientIdentifier("client-1"),
        basis=np.eye(4)[:, :2],
        transition_vector=np.ones(4),
        covariance=np.eye(4),
        support_before=2,
        support_after=2,
        beta=1.2,
        eigengap_ratio=2.0,
        selected_rank=2,
        control_diagnostics_passed=True,
    )
    reason = validate_summary(summary, minimum_support=5)
    assert reason is not None
