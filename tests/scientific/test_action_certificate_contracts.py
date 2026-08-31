from __future__ import annotations

from fedact.core.certification import (
    DomainValid,
    decide,
)
from fedact.domain.enums import CertificationStatus


def test_action_certificate_requires_worst_case_lower_bound() -> None:
    decision = decide(
        lower=0.4,
        upper=1.0,
        tau_align=0.2,
        tau_amb=0.8,
        domain_valid=DomainValid(True),
        diameter_bound=1.0,
        diameter_quantile=2.0,
    )
    assert decision.status is CertificationStatus.CERTIFIED_POSITIVE
