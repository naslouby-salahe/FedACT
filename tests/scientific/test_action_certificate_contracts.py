from __future__ import annotations

from fedact.fedact.certification import (
    CertificateState,
    DomainValid,
    decide,
)


def test_action_certificate_requires_worst_case_lower_bound() -> None:
    decision = decide(
        lower=0.4,
        upper=1.0,
        tau_align=0.2,
        tau_amb=0.8,
        domain_valid=DomainValid(True),
    )
    assert decision.state is CertificateState.CERTIFIED
