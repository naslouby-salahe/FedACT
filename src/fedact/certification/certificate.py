from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

import numpy as np
import torch

from fedact.certification.actions import ActionInterval
from fedact.domain.types import (
    AbstentionReason,
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

_DIAMETER_DOUBLING_FACTOR: Final = 2.0


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
        required_agreement_count=req,
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
    uncertainty_radius: ThresholdValue
    beta: ThresholdValue
    selected_rank: RankDimension
    control_diagnostics_passed: ValidationFlag
    subspace: torch.Tensor | None = None
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
    uncertainty_radius: ThresholdValue
    beta: ThresholdValue
    subspace: torch.Tensor | np.ndarray | None = None
    projector: np.ndarray | None = None
    covariance: np.ndarray | None = None


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
    if vertices <= 0:
        raise ValueError("constraint intersection requires a positive vertex budget")
    plausibility_ball: L2Ball | None = None
    constraints_list: list[ClientConstraint] = []
    for arg in args:
        if isinstance(arg, L2Ball):
            plausibility_ball = arg
        elif isinstance(arg, (list, tuple)):
            constraints_list.extend(arg)

    subs: list[torch.Tensor] = [
        torch.tensor(c.subspace, dtype=torch.float32)
        if isinstance(c.subspace, np.ndarray)
        else (c.subspace if c.subspace is not None else torch.empty((0, 0)))
        for c in constraints_list
    ]
    rads = [c.uncertainty_radius for c in constraints_list]
    uncertainty_diameter = _DIAMETER_DOUBLING_FACTOR * sum(rads)
    diameter = (
        min(uncertainty_diameter, _DIAMETER_DOUBLING_FACTOR * plausibility_ball.radius)
        if plausibility_ball is not None
        else uncertainty_diameter
    )
    return FeasibleSet(
        nuisance_subspaces=tuple(subs),
        uncertainty_radii=tuple(rads),
        diameter=diameter,
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
        if target.size == 0:
            raise ValueError("Chebyshev center requires at least one point")
        center = np.mean(target, axis=0)
        radius = float(np.max(np.linalg.norm(target - center, axis=1)))
        return ChebyshevCenterResult(center=center, radius=radius)
    if isinstance(target, FeasibleSet):
        if target.center is not None:
            center = (
                target.center.detach().cpu().numpy()
                if isinstance(target.center, torch.Tensor)
                else target.center
            )
        elif target.plausibility_ball is not None:
            center = (
                target.plausibility_ball.center.detach().cpu().numpy()
                if isinstance(target.plausibility_ball.center, torch.Tensor)
                else target.plausibility_ball.center
            )
        else:
            dimension = target.nuisance_subspaces[0].shape[0] if target.nuisance_subspaces else 0
            center = np.zeros(dimension)
        return ChebyshevCenterResult(
            center=center, radius=target.diameter / _DIAMETER_DOUBLING_FACTOR
        )
    if not target:
        raise ValueError("Chebyshev center requires at least one constraint")
    dimension = next(
        (constraint.subspace.shape[0] for constraint in target if constraint.subspace is not None),
        0,
    )
    return ChebyshevCenterResult(
        center=np.zeros(dimension),
        radius=sum(constraint.uncertainty_radius for constraint in target),
    )


def minimum_uniform_inflation(
    *args: L2Ball | Sequence[ClientConstraint],
    vertices: SampleCount,
) -> CoordinateValue:
    if vertices <= 0:
        raise ValueError("uniform inflation requires a positive vertex budget")
    plausibility_ball = next((arg for arg in args if isinstance(arg, L2Ball)), None)
    constraints = tuple(
        constraint for arg in args if isinstance(arg, (list, tuple)) for constraint in arg
    )
    if plausibility_ball is None or not constraints:
        raise ValueError("uniform inflation requires a plausibility ball and client constraints")
    center = (
        plausibility_ball.center.detach().cpu().numpy()
        if isinstance(plausibility_ball.center, torch.Tensor)
        else plausibility_ball.center
    )
    requirements: list[CoordinateValue] = []
    for constraint in constraints:
        if constraint.projector is None:
            continue
        residual = center - constraint.projector @ center
        requirements.append(float(np.linalg.norm(residual)) / constraint.uncertainty_radius)
    return max((1.0, *requirements))


def build_nuisance_spaces(
    nuisance_subspaces: Sequence[torch.Tensor],
    uncertainty_radii: Sequence[ThresholdValue],
    geometry: FederationGeometry = FederationGeometry.COMPLEMENTARY,
) -> FeasibleSet:
    if len(nuisance_subspaces) != len(uncertainty_radii):
        raise ValueError("each nuisance subspace requires a matching uncertainty radius")
    if not nuisance_subspaces:
        raise ValueError("feasible-set construction requires client nuisance subspaces")
    _unused = geometry
    return FeasibleSet(
        nuisance_subspaces=tuple(nuisance_subspaces),
        uncertainty_radii=tuple(uncertainty_radii),
        diameter=_DIAMETER_DOUBLING_FACTOR * sum(uncertainty_radii),
    )


def compute_chebyshev_center(feasible_set: FeasibleSet) -> torch.Tensor:
    if feasible_set.center is not None:
        return (
            feasible_set.center
            if isinstance(feasible_set.center, torch.Tensor)
            else torch.tensor(feasible_set.center, dtype=torch.float32)
        )
    if not feasible_set.nuisance_subspaces:
        raise ValueError("Chebyshev center requires nuisance subspaces or an explicit center")
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
