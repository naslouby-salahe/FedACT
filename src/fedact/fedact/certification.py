from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from fedact.domain.enums import CertificationStatus
from fedact.domain.types import (
    CertificationFlag,
    DiagnosisMessage,
    EvaluationCount,
    GateComplianceFlag,
    IntervalBound,
    MetricRate,
    NormValue,
    StabilityFlag,
    ThresholdValue,
    ValidationFlag,
)
from fedact.fedact.estimand import ActionInterval


class CertificateState(StrEnum):
    CERTIFIED = "CERTIFIED"
    AMBIGUOUS = "AMBIGUOUS"
    NEGATIVE = "NEGATIVE"
    ABSTAIN = "ABSTAIN"


@dataclass(frozen=True)
class DomainValid:
    valid: ValidationFlag


@dataclass(frozen=True)
class CertificateDecision:
    status: CertificationStatus
    lower_bound: IntervalBound
    upper_bound: IntervalBound
    width: IntervalBound
    alignment_threshold: ThresholdValue
    ambiguity_width_threshold: ThresholdValue
    diameter_gate_passed: bool
    leave_one_client_out_passed: bool
    leave_one_client_out_note: DiagnosisMessage | None

    @property
    def state(self) -> CertificateState:
        if self.status is CertificationStatus.CERTIFIED_POSITIVE:
            return CertificateState.CERTIFIED
        if self.status is CertificationStatus.CERTIFIED_NEGATIVE:
            return CertificateState.NEGATIVE
        if self.status is CertificationStatus.AMBIGUOUS:
            return CertificateState.AMBIGUOUS
        return CertificateState.ABSTAIN


def decide(
    lower: IntervalBound,
    upper: IntervalBound,
    tau_align: ThresholdValue,
    tau_amb: ThresholdValue,
    domain_valid: DomainValid,
    diameter_bound: IntervalBound,
    diameter_quantile: ThresholdValue,
) -> CertificateDecision:
    interval = ActionInterval(lower=lower, upper=upper)
    return certify_action_interval(
        action_interval=interval,
        domain_validity=domain_valid,
        alignment_threshold=tau_align,
        ambiguity_width_threshold=tau_amb,
        set_diameter=diameter_bound,
        historical_realized_diameter_quantile=diameter_quantile,
    )


def is_forecast_set_within_gate(
    diameter_bound: IntervalBound,
    historical_quantile_value: ThresholdValue,
) -> GateComplianceFlag:
    return diameter_bound <= historical_quantile_value


@dataclass(frozen=True)
class LeaveOneClientOutStabilityOutcome:
    is_stable: StabilityFlag
    required_agreement_count: EvaluationCount


def leave_one_client_out_stability(
    decisions: Sequence[CertificationFlag],
    minimum_unchanged_fraction: MetricRate,
) -> LeaveOneClientOutStabilityOutcome:
    if not decisions:
        return LeaveOneClientOutStabilityOutcome(is_stable=True, required_agreement_count=0)
    trues = sum(1 for d in decisions if d)
    falses = len(decisions) - trues
    dominant = max(trues, falses)
    req = int(math.ceil(len(decisions) * minimum_unchanged_fraction))
    return LeaveOneClientOutStabilityOutcome(
        is_stable=dominant >= req,
        required_agreement_count=int(len(decisions) * minimum_unchanged_fraction),
    )


def downgrade_dominant_single_client(state: CertificateState) -> CertificateState:
    if state is CertificateState.CERTIFIED:
        return CertificateState.AMBIGUOUS
    return state


def certify_action_interval(
    action_interval: ActionInterval,
    domain_validity: DomainValid,
    alignment_threshold: ThresholdValue,
    ambiguity_width_threshold: ThresholdValue,
    set_diameter: NormValue,
    historical_realized_diameter_quantile: ThresholdValue,
    leave_one_client_out_passed: ValidationFlag = True,
    leave_one_client_out_note: DiagnosisMessage | None = None,
) -> CertificateDecision:
    if not domain_validity.valid or not leave_one_client_out_passed:
        return CertificateDecision(
            status=CertificationStatus.ABSTAIN,
            lower_bound=action_interval.lower,
            upper_bound=action_interval.upper,
            width=action_interval.width,
            alignment_threshold=alignment_threshold,
            ambiguity_width_threshold=ambiguity_width_threshold,
            diameter_gate_passed=False,
            leave_one_client_out_passed=leave_one_client_out_passed,
            leave_one_client_out_note=leave_one_client_out_note,
        )
    diameter_ok = set_diameter <= historical_realized_diameter_quantile
    if not diameter_ok:
        return CertificateDecision(
            status=CertificationStatus.ABSTAIN,
            lower_bound=action_interval.lower,
            upper_bound=action_interval.upper,
            width=action_interval.width,
            alignment_threshold=alignment_threshold,
            ambiguity_width_threshold=ambiguity_width_threshold,
            diameter_gate_passed=False,
            leave_one_client_out_passed=leave_one_client_out_passed,
            leave_one_client_out_note=leave_one_client_out_note,
        )
    if action_interval.is_certified_positive(alignment_threshold, ambiguity_width_threshold):
        status = CertificationStatus.CERTIFIED_POSITIVE
    elif action_interval.is_certified_negative(alignment_threshold, ambiguity_width_threshold):
        status = CertificationStatus.CERTIFIED_NEGATIVE
    else:
        status = CertificationStatus.AMBIGUOUS
    return CertificateDecision(
        status=status,
        lower_bound=action_interval.lower,
        upper_bound=action_interval.upper,
        width=action_interval.width,
        alignment_threshold=alignment_threshold,
        ambiguity_width_threshold=ambiguity_width_threshold,
        diameter_gate_passed=True,
        leave_one_client_out_passed=leave_one_client_out_passed,
        leave_one_client_out_note=leave_one_client_out_note,
    )
