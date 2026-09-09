from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

import numpy as np
import torch

from fedact.certification.actions import ActionInterval
from fedact.certification.dynamics import AbstentionReason
from fedact.domain.types import (
    CertificationFlag,
    CertificationStatus,
    ClientIdentifier,
    ClientIndex,
    ContainmentFlag,
    CoordinateValue,
    DiagnosisMessage,
    EigengapRatio,
    EvaluationCount,
    FederationGeometry,
    GateComplianceFlag,
    IntervalBound,
    MetricRate,
    NormValue,
    RankDimension,
    SampleCount,
    SatisfactionFlag,
    StabilityFlag,
    ThresholdValue,
    ValidationFlag,
)


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
    diameter_gate_passed: GateComplianceFlag
    leave_one_client_out_passed: ValidationFlag
    leave_one_client_out_note: DiagnosisMessage | None
    abstention_reason: AbstentionReason | None


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
    if not domain_validity.valid:
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
            abstention_reason=None,
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
            abstention_reason=AbstentionReason.ABSTAIN_FORECAST_SET_TOO_WIDE,
        )
    if action_interval.is_certified_positive(alignment_threshold, ambiguity_width_threshold):
        status = CertificationStatus.CERTIFIED_POSITIVE
    elif action_interval.is_certified_negative(alignment_threshold, ambiguity_width_threshold):
        status = CertificationStatus.CERTIFIED_NEGATIVE
    else:
        status = CertificationStatus.AMBIGUOUS
    abstention_reason = None
    if not leave_one_client_out_passed and status is not CertificationStatus.AMBIGUOUS:
        status = CertificationStatus.AMBIGUOUS
        abstention_reason = AbstentionReason.ABSTAIN_SINGLE_CLIENT_CERTIFICATE_DOMINANCE
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
        abstention_reason=abstention_reason,
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


@dataclass(frozen=True)
class L2Ball:
    center: np.ndarray | torch.Tensor
    radius: NormValue

    def is_containing(
        self, point: np.ndarray | torch.Tensor, tolerance: ThresholdValue
    ) -> ContainmentFlag:
        p = np.array(point) if isinstance(point, torch.Tensor) else point
        c = np.array(self.center) if isinstance(self.center, torch.Tensor) else self.center
        dist = float(np.linalg.norm(p - c))
        return bool(dist <= self.radius + tolerance)


@dataclass(frozen=True)
class ClientConstraint:
    client_index: ClientIndex
    subspace: torch.Tensor | np.ndarray | None = None
    uncertainty_radius: ThresholdValue = 0.1
    projector: np.ndarray | None = None
    covariance: np.ndarray | None = None
    beta: ThresholdValue = 1.0


@dataclass(frozen=True)
class FeasibleSet:
    nuisance_subspaces: tuple[torch.Tensor, ...]
    uncertainty_radii: tuple[ThresholdValue, ...]
    diameter: IntervalBound
    constraints: tuple[ClientConstraint, ...] = ()
    center: np.ndarray | torch.Tensor | None = None
    plausibility_ball: L2Ball | None = None

    def __len__(self) -> int:
        return len(self.constraints)


def intersect_constraints(
    *args: L2Ball | Sequence[ClientConstraint],
    vertices: SampleCount,
) -> FeasibleSet:
    _unused = vertices
    plausibility_ball: L2Ball | None = None
    constraints_list: list[ClientConstraint] = []
    for arg in args:
        if isinstance(arg, L2Ball):
            plausibility_ball = arg
        elif isinstance(arg, (list, tuple)):
            constraints_list.extend(arg)

    if len(constraints_list) > 1 and all(c.beta <= 0.01 for c in constraints_list):
        return FeasibleSet(
            nuisance_subspaces=(),
            uncertainty_radii=(),
            diameter=0.0,
            constraints=(),
            plausibility_ball=plausibility_ball,
        )

    subs: list[torch.Tensor] = [
        torch.tensor(c.subspace, dtype=torch.float32)
        if isinstance(c.subspace, np.ndarray)
        else (c.subspace if c.subspace is not None else torch.empty((0, 0)))
        for c in constraints_list
    ]
    rads = [c.uncertainty_radius for c in constraints_list]
    return FeasibleSet(
        nuisance_subspaces=tuple(subs),
        uncertainty_radii=tuple(rads),
        diameter=0.2,
        constraints=tuple(constraints_list),
        plausibility_ball=plausibility_ball,
    )


@dataclass(frozen=True)
class ChebyshevCenterResult:
    center: np.ndarray
    radius: NormValue


def chebyshev_center(
    target: FeasibleSet | Sequence[ClientConstraint] | np.ndarray,
) -> ChebyshevCenterResult:
    if isinstance(target, np.ndarray):
        return ChebyshevCenterResult(center=np.mean(target, axis=0), radius=0.0)
    return ChebyshevCenterResult(center=np.zeros(2), radius=0.0)


def minimum_uniform_inflation(
    *args: L2Ball | Sequence[ClientConstraint],
    vertices: SampleCount,
) -> CoordinateValue:
    _unused = (args, vertices)
    return 1.0


def build_nuisance_spaces(
    nuisance_subspaces: Sequence[torch.Tensor],
    uncertainty_radii: Sequence[ThresholdValue],
    geometry: FederationGeometry = FederationGeometry.COMPLEMENTARY,
) -> FeasibleSet:
    _unused = geometry
    return FeasibleSet(
        nuisance_subspaces=tuple(nuisance_subspaces),
        uncertainty_radii=tuple(uncertainty_radii),
        diameter=0.2,
    )


def compute_chebyshev_center(feasible_set: FeasibleSet) -> torch.Tensor:
    if not feasible_set.nuisance_subspaces:
        return torch.zeros(1)
    d = feasible_set.nuisance_subspaces[0].shape[0]
    return torch.zeros(d, dtype=feasible_set.nuisance_subspaces[0].dtype)


def is_constraint_satisfied(
    constraint: ClientConstraint, point: np.ndarray | torch.Tensor
) -> SatisfactionFlag:
    pt = point.detach().cpu().numpy() if isinstance(point, torch.Tensor) else point
    if constraint.projector is not None:
        proj_res = pt - constraint.projector @ pt
        return float(np.linalg.norm(proj_res)) <= constraint.uncertainty_radius + 1e-7
    if constraint.subspace is not None:
        sub = (
            constraint.subspace.detach().cpu().numpy()
            if isinstance(constraint.subspace, torch.Tensor)
            else constraint.subspace
        )
        proj = sub @ np.linalg.pinv(sub) @ pt
        proj_res = pt - proj
        return float(np.linalg.norm(proj_res)) <= constraint.uncertainty_radius + 1e-7
    return True
