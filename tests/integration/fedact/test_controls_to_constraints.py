from __future__ import annotations

import numpy as np

from fedact.fedact.constraints import ClientConstraintSummary, validate_summary
from fedact.fedact.controls import build_control_displacement
from fedact.fedact.transitions import ClientIdentifier


def test_controls_to_constraints_integration() -> None:
    prior = np.zeros(4)
    recent = np.ones(4)
    disp = build_control_displacement(prior, recent)
    summary = ClientConstraintSummary(
        client_id=ClientIdentifier("client-test"),
        basis=np.eye(4)[:, :2],
        transition_vector=disp,
        covariance=np.eye(4),
        support_before=10,
        support_after=10,
        beta=1.0,
        eigengap_ratio=2.0,
        selected_rank=2,
        control_diagnostics_passed=True,
    )
    reason = validate_summary(summary, minimum_support=5)
    assert reason is None
