from __future__ import annotations

from fedact.fedact.certification import (
    CertificateState,
    DomainValid,
    decide,
    downgrade_dominant_single_client,
    is_forecast_set_within_gate,
    leave_one_client_out_stability,
)


def test_decide_certifies_positive_bounded_interval() -> None:
    decision = decide(
        lower=0.5,
        upper=1.2,
        tau_align=0.3,
        tau_amb=1.0,
        domain_valid=DomainValid(True),
    )
    assert decision.state is CertificateState.CERTIFIED


def test_decide_classifies_ambiguous() -> None:
    decision = decide(
        lower=0.1,
        upper=2.0,
        tau_align=0.3,
        tau_amb=1.0,
        domain_valid=DomainValid(True),
    )
    assert decision.state is CertificateState.AMBIGUOUS


def test_leave_one_client_out_stability() -> None:
    decisions = (True,) * 9 + (False,)
    outcome = leave_one_client_out_stability(decisions, minimum_unchanged_fraction=0.8)
    assert outcome.is_stable
    assert outcome.required_agreement_count == 8


def test_is_forecast_set_within_gate() -> None:
    assert is_forecast_set_within_gate(diameter_bound=2.0, historical_quantile_value=3.0)
    assert not is_forecast_set_within_gate(diameter_bound=4.0, historical_quantile_value=3.0)


def test_downgrade_dominant_single_client() -> None:
    assert (
        downgrade_dominant_single_client(CertificateState.CERTIFIED) is CertificateState.AMBIGUOUS
    )
    assert downgrade_dominant_single_client(CertificateState.NEGATIVE) is CertificateState.NEGATIVE
