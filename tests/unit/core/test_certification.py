from __future__ import annotations

from fedact.core.actions import ActionInterval
from fedact.core.certification import (
    DomainValid,
    certify_action_interval,
    decide,
    is_forecast_set_within_gate,
    leave_one_client_out_stability,
)
from fedact.core.transitions import AbstentionReason
from fedact.domain.enums import CertificationStatus


def test_decide_certifies_positive_bounded_interval() -> None:
    decision = decide(
        lower=0.5,
        upper=1.2,
        tau_align=0.3,
        tau_amb=1.0,
        domain_valid=DomainValid(True),
        diameter_bound=1.0,
        diameter_quantile=2.0,
    )
    assert decision.status is CertificationStatus.CERTIFIED_POSITIVE


def test_decide_classifies_ambiguous() -> None:
    decision = decide(
        lower=0.1,
        upper=2.0,
        tau_align=0.3,
        tau_amb=1.0,
        domain_valid=DomainValid(True),
        diameter_bound=1.0,
        diameter_quantile=2.0,
    )
    assert decision.status is CertificationStatus.AMBIGUOUS


def test_leave_one_client_out_stability() -> None:
    decisions = (True,) * 9 + (False,)
    outcome = leave_one_client_out_stability(decisions, minimum_unchanged_fraction=0.8)
    assert outcome.is_stable
    assert outcome.required_agreement_count == 8


def test_is_forecast_set_within_gate() -> None:
    assert is_forecast_set_within_gate(diameter_bound=2.0, historical_quantile_value=3.0)
    assert not is_forecast_set_within_gate(diameter_bound=4.0, historical_quantile_value=3.0)


def test_leave_one_client_out_failure_downgrades_certified_to_ambiguous() -> None:
    decision = certify_action_interval(
        action_interval=ActionInterval(lower=0.5, upper=1.2),
        domain_validity=DomainValid(True),
        alignment_threshold=0.3,
        ambiguity_width_threshold=1.0,
        set_diameter=1.0,
        historical_realized_diameter_quantile=2.0,
        leave_one_client_out_passed=False,
    )
    assert decision.status is CertificationStatus.AMBIGUOUS
    assert (
        decision.abstention_reason is AbstentionReason.ABSTAIN_SINGLE_CLIENT_CERTIFICATE_DOMINANCE
    )


def test_leave_one_client_out_failure_leaves_ambiguous_decision_unmarked() -> None:
    decision = certify_action_interval(
        action_interval=ActionInterval(lower=0.1, upper=2.0),
        domain_validity=DomainValid(True),
        alignment_threshold=0.3,
        ambiguity_width_threshold=1.0,
        set_diameter=1.0,
        historical_realized_diameter_quantile=2.0,
        leave_one_client_out_passed=False,
    )
    assert decision.status is CertificationStatus.AMBIGUOUS
    assert decision.abstention_reason is None


def test_forecast_set_too_wide_carries_abstention_reason() -> None:
    decision = certify_action_interval(
        action_interval=ActionInterval(lower=0.5, upper=1.2),
        domain_validity=DomainValid(True),
        alignment_threshold=0.3,
        ambiguity_width_threshold=1.0,
        set_diameter=5.0,
        historical_realized_diameter_quantile=2.0,
    )
    assert decision.status is CertificationStatus.ABSTAIN
    assert decision.abstention_reason is AbstentionReason.ABSTAIN_FORECAST_SET_TOO_WIDE
