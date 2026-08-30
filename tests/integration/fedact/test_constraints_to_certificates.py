from __future__ import annotations

import numpy as np

from fedact.domain.enums import CertificationStatus
from fedact.fedact.actions import action_support_bounds
from fedact.fedact.certification import DomainValid, decide


def test_constraints_to_certificates_integration() -> None:
    direction = np.array([1.0, 0.0])
    vertices = (np.array([0.8, 0.0]), np.array([1.2, 0.0]))
    interval = action_support_bounds(direction, vertices)
    decision = decide(
        lower=interval.lower,
        upper=interval.upper,
        tau_align=0.5,
        tau_amb=1.0,
        domain_valid=DomainValid(True),
        diameter_bound=1.0,
        diameter_quantile=2.0,
    )
    assert decision.status is CertificationStatus.CERTIFIED_POSITIVE
