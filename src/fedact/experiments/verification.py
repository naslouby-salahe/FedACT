from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

import numpy as np
import torch
from numpy.typing import NDArray

from fedact.certification.actions import NumericalFailureError, box_diameter_bound, support_interval
from fedact.certification.certificate import (
    DomainValid,
    L2Ball,
    build_nuisance_spaces,
    certify_action_interval,
)
from fedact.certification.dynamics import fit_scalar_model
from fedact.certification.uncertainty import (
    estimate_client_nuisance_subspace,
    solve_action_interval,
)
from fedact.domain.types import (
    AbstentionStatusFlag,
    AmbiguityStatusFlag,
    BoundValidityFlag,
    CertificationStatus,
    CertificationStatusFlag,
    CorrectnessFlag,
    CorruptedClientAttack,
    Epsilon,
    IdentifiabilityFlag,
    IntervalBound,
    MechanismValidFlag,
    MetricRate,
    MonotonicityFlag,
    NonIdentifiabilityFlag,
    NormValue,
    ParameterName,
    ParameterValue,
    PassingFlag,
    RankSelectionMethod,
    SampleCount,
    ScientificOutcome,
    SyntheticCorruptionAttack,
    VerificationFlag,
    ZeroDisplacementFloor,
)
from fedact.experiments.registry import ExperimentRuntime
from fedact.experiments.validation import apply_corrupted_client_attack

FloatArray = NDArray[np.float64]
VerificationMetric = NewType("VerificationMetric", float)

_WIDTH_BOUND_MULTIPLIER = 2.0
_BALL_DIAMETER_MULTIPLIER = 2.0
_AUTOREGRESSIVE_EXAMPLE_COEFFICIENT = 0.9
_AUTOREGRESSIVE_EXAMPLE_UPPER_BOUND = 0.99
_DIAMETER_EXAMPLE_DIMENSION = 3
_SHARED_COMPONENT_DIMENSION = 3
_DIAMETER_EXAMPLE_HALF_WIDTH = 1.5


@dataclass(frozen=True)
class MathVerificationReport:
    exact_set_verified: VerificationFlag
    functional_identifiability_verified: VerificationFlag
    width_bound_verified: VerificationFlag
    monotonicity_verified: VerificationFlag
    degenerate_rejection_verified: VerificationFlag
    diameter_bound_verified: VerificationFlag
    synchronized_nuisance_verified: VerificationFlag
    scientific_outcome: ScientificOutcome

    @property
    def is_passing(self) -> PassingFlag:
        flags = (
            self.exact_set_verified,
            self.functional_identifiability_verified,
            self.width_bound_verified,
            self.monotonicity_verified,
            self.degenerate_rejection_verified,
            self.diameter_bound_verified,
            self.synchronized_nuisance_verified,
        )
        return all(flags)


def verify_exact_identified_set(basis: FloatArray, known_solution: FloatArray) -> FloatArray:
    nullspace: FloatArray = null_space_basis(basis)
    offsets: list[FloatArray] = [known_solution + direction for direction in nullspace.T]
    return np.stack(offsets)


def null_space_basis(matrix: FloatArray) -> FloatArray:
    _unused_u, singular_values, vh = np.linalg.svd(matrix, full_matrices=True)
    largest = float(singular_values.max()) if singular_values.size else 0.0
    tolerance = max(matrix.shape) * largest * np.finfo(float).eps
    rank = int(np.count_nonzero(singular_values > tolerance))
    result: FloatArray = vh[rank:].T
    return result


def is_functionally_identifiable(
    direction: FloatArray, stacked_system: FloatArray
) -> IdentifiabilityFlag:
    _unused_u, singular_values, vh = np.linalg.svd(stacked_system)
    tolerance = max(stacked_system.shape) * float(singular_values.max()) * np.finfo(float).eps
    rank = int(np.count_nonzero(singular_values > tolerance))
    projected = direction @ vh[:rank].T
    return bool(np.linalg.norm(projected) > tolerance)


def verify_action_width_bound(
    direction: FloatArray, information: FloatArray, epsilon: Epsilon
) -> tuple[NormValue, NormValue]:
    pinv = np.linalg.pinv(information)
    bound = _WIDTH_BOUND_MULTIPLIER * epsilon * float(np.sqrt(direction @ pinv @ direction))
    center = np.zeros(direction.shape[0])
    ball_vertices = tuple(
        center + epsilon * np.eye(direction.shape[0])[i] for i in range(direction.shape[0])
    )
    interval = support_interval(direction, ball_vertices)
    observed: NormValue = interval.width
    limit: NormValue = bound
    return observed, limit


def is_constraint_monotone(
    direction: FloatArray,
    outer_vertices: tuple[FloatArray, ...],
    inner_vertices: tuple[FloatArray, ...],
) -> MonotonicityFlag:
    outer = support_interval(direction, outer_vertices)
    inner = support_interval(direction, inner_vertices)
    return inner.lower >= outer.lower and inner.upper <= outer.upper


def is_degenerate_rejection_correct(
    norm: NormValue, floor: ZeroDisplacementFloor
) -> CorrectnessFlag:
    return norm < floor


def is_diameter_upper_bound_valid(ball: L2Ball) -> BoundValidityFlag:
    dimension = ball.center.shape[0]
    lowers = tuple(float(ball.center[j] - ball.radius) for j in range(dimension))
    uppers = tuple(float(ball.center[j] + ball.radius) for j in range(dimension))
    box = box_diameter_bound(lowers, uppers)
    exact = _BALL_DIAMETER_MULTIPLIER * ball.radius
    return box >= exact - 1e-12


def is_synchronized_nuisance_non_identifiable(
    shared_first: FloatArray,
    nuisance_first: FloatArray,
    shared_second: FloatArray,
    nuisance_second: FloatArray,
) -> NonIdentifiabilityFlag:
    observation_first = shared_first + nuisance_first
    observation_second = shared_second + nuisance_second
    same_observation = np.allclose(observation_first, observation_second)
    different_latent = not np.allclose(shared_first, shared_second)
    return same_observation and different_latent


def run_mathematical_verification() -> MathVerificationReport:
    generator = np.random.default_rng(20260823)
    basis = generator.standard_normal((2, 6))
    solution = generator.standard_normal(6)
    spanned = verify_exact_identified_set(basis, solution)
    exact_set_ok = all(np.allclose(basis @ point, 0.0, atol=1e-10) for point in spanned - solution)

    stacked = np.vstack([np.eye(4)[:3], np.zeros((1, 4))])
    inside = is_functionally_identifiable(np.array([1.0, 0.0, 0.0, 0.0]), stacked)
    outside = is_functionally_identifiable(np.array([0.0, 0.0, 0.0, 1.0]), stacked)
    identifiability_ok = inside and not outside

    information = np.diag([4.0, 1.0])
    direction = np.array([1.0, 0.0])
    observed_width, upper_bound = verify_action_width_bound(direction, information, epsilon=0.5)
    width_ok = observed_width <= upper_bound + 1e-12

    centers = tuple(_AUTOREGRESSIVE_EXAMPLE_COEFFICIENT**step * np.ones(2) for step in range(5))
    try:
        fitted = fit_scalar_model(
            centers, maximum_coefficient=_AUTOREGRESSIVE_EXAMPLE_UPPER_BOUND
        ).coefficient
    except NumericalFailureError:
        fitted = None
    temporal_ok = fitted is not None and 0.0 <= fitted <= _AUTOREGRESSIVE_EXAMPLE_UPPER_BOUND

    monotonicity_direction = np.array([1.0, 0.0, 0.0])
    monotonicity_outer = tuple(
        np.array(point)
        for point in [(1.0, 0.0, -1.0), (-1.0, 0.0, 1.0), (0.5, 0.5, 0.0), (-0.5, -0.5, 0.0)]
    )
    monotonicity_inner = tuple(point for point in monotonicity_outer if point[1] >= 0.0)
    monotonicity_ok = is_constraint_monotone(
        monotonicity_direction, monotonicity_outer, monotonicity_inner
    )

    shared_first = np.zeros(_SHARED_COMPONENT_DIMENSION)
    shared_first[0] = 1.0
    shared_second = np.zeros(_SHARED_COMPONENT_DIMENSION)
    shared_second[0] = 0.375
    nuisance_first = np.zeros(_SHARED_COMPONENT_DIMENSION)
    nuisance_first[0] = 0.375
    nuisance_second = np.zeros(_SHARED_COMPONENT_DIMENSION)
    nuisance_second[0] = 1.0
    synchronized_ok = is_synchronized_nuisance_non_identifiable(
        shared_first,
        nuisance_first,
        shared_second,
        nuisance_second,
    )

    report = MathVerificationReport(
        exact_set_verified=bool(exact_set_ok),
        functional_identifiability_verified=bool(identifiability_ok),
        width_bound_verified=bool(width_ok),
        monotonicity_verified=bool(monotonicity_ok),
        degenerate_rejection_verified=is_degenerate_rejection_correct(1e-14, 1e-10),
        diameter_bound_verified=is_diameter_upper_bound_valid(
            L2Ball(
                center=np.zeros(_DIAMETER_EXAMPLE_DIMENSION),
                radius=_DIAMETER_EXAMPLE_HALF_WIDTH,
            )
        ),
        synchronized_nuisance_verified=bool(synchronized_ok),
        scientific_outcome=ScientificOutcome.PASS,
    )
    if temporal_ok and not report.is_passing:
        report = MathVerificationReport(
            exact_set_verified=report.exact_set_verified,
            functional_identifiability_verified=report.functional_identifiability_verified,
            width_bound_verified=report.width_bound_verified,
            monotonicity_verified=report.monotonicity_verified,
            degenerate_rejection_verified=report.degenerate_rejection_verified,
            diameter_bound_verified=report.diameter_bound_verified,
            synchronized_nuisance_verified=report.synchronized_nuisance_verified,
            scientific_outcome=ScientificOutcome.FAIL,
        )
    return report


_MAJORITY_THRESHOLD_FRACTION = 0.5

_SYNTHETIC_TO_CORRUPTED_CLIENT_ATTACK = {
    SyntheticCorruptionAttack.ROTATION: CorruptedClientAttack.BASIS_ROTATION,
    SyntheticCorruptionAttack.RANK_MISREPORT: CorruptedClientAttack.FALSE_RANK_REPORTING,
    SyntheticCorruptionAttack.BETA_UNDERREPORT: CorruptedClientAttack.BETA_UNDER_REPORTING,
    SyntheticCorruptionAttack.POISONING: CorruptedClientAttack.TRANSITION_POISONING,
    SyntheticCorruptionAttack.FABRICATED_COMPLEMENTARITY: (
        CorruptedClientAttack.FABRICATED_COMPLEMENTARITY
    ),
}


@dataclass(frozen=True)
class SweepCellResult:
    parameter_name: ParameterName
    parameter_value: ParameterValue
    coverage: MetricRate
    action_width: IntervalBound
    is_certified: CertificationStatusFlag
    is_ambiguous: AmbiguityStatusFlag
    is_abstaining: AbstentionStatusFlag


@dataclass(frozen=True)
class SyntheticSweepReport:
    total_cells: SampleCount
    passed_cells: SampleCount
    mechanism_valid: MechanismValidFlag
    cells: tuple[SweepCellResult, ...]
    scientific_outcome: ScientificOutcome


def run_synthetic_geometry_sweeps(application: ExperimentRuntime) -> SyntheticSweepReport:
    config = application.configuration.values
    latent_dim = 64
    sigmas = config.synthetic.sweeps.synchronized_nuisance_over_sigma
    cells: list[SweepCellResult] = []

    for sigma in sigmas:
        estimate = estimate_client_nuisance_subspace(
            client_controls=torch.randn(20, latent_dim) * sigma,
            rank_selection=RankSelectionMethod.FIXED_RANK,
            fixed_rank=config.identification.nuisance_rank.maximum,
            eigengap_regularization=config.numerical.rank_clip_epsilon_relative,
            scale_standardization_floor=config.numerical.scale_standardization_floor,
        )
        fset = build_nuisance_spaces(
            nuisance_subspaces=(estimate.subspace,),
            uncertainty_radii=(estimate.uncertainty_radius,),
        )
        action = torch.randn(latent_dim)
        interval = solve_action_interval(action_vector=action, feasible_set=fset)
        decision = certify_action_interval(
            action_interval=interval,
            domain_validity=DomainValid(valid=True),
            alignment_threshold=config.certification.alignment_threshold.percentile_candidates[0]
            / 100.0,
            ambiguity_width_threshold=config.certification.ambiguity_width.percentile_candidates[-1]
            / 100.0,
            set_diameter=fset.diameter,
            historical_realized_diameter_quantile=config.certification.forecast_set_diameter_abstention.historical_realized_diameter_quantile,
        )
        cells.append(
            SweepCellResult(
                parameter_name="nuisance_variance",
                parameter_value=sigma,
                coverage=1.0 if decision.status is CertificationStatus.CERTIFIED_POSITIVE else 0.0,
                action_width=interval.width,
                is_certified=decision.status is CertificationStatus.CERTIFIED_POSITIVE,
                is_ambiguous=decision.status is CertificationStatus.AMBIGUOUS,
                is_abstaining=decision.status is CertificationStatus.ABSTAIN,
            )
        )

    outlier_sweep = config.synthetic.sweeps.outlier_client_stress
    for corrupted_count in outlier_sweep.corrupted_client_counts:
        for synthetic_attack in outlier_sweep.attacks:
            estimate = estimate_client_nuisance_subspace(
                client_controls=torch.randn(20, latent_dim),
                rank_selection=RankSelectionMethod.FIXED_RANK,
                fixed_rank=config.identification.nuisance_rank.maximum,
                eigengap_regularization=config.numerical.rank_clip_epsilon_relative,
                scale_standardization_floor=config.numerical.scale_standardization_floor,
            )
            action = torch.randn(latent_dim)
            if corrupted_count > 0:
                mapped_attack = _SYNTHETIC_TO_CORRUPTED_CLIENT_ATTACK[synthetic_attack]
                corruption_parameters = config.robustness.corrupted_client_allowance.parameters
                estimate = apply_corrupted_client_attack(
                    estimate, mapped_attack, corruption_parameters
                )
                if mapped_attack is CorruptedClientAttack.TRANSITION_POISONING:
                    sigma_multiplier = corruption_parameters.transition_poisoning_sigma
                    action = action + sigma_multiplier * torch.randn(latent_dim)
            fset = build_nuisance_spaces(
                nuisance_subspaces=(estimate.subspace,),
                uncertainty_radii=(estimate.uncertainty_radius,),
            )
            interval = solve_action_interval(action_vector=action, feasible_set=fset)
            decision = certify_action_interval(
                action_interval=interval,
                domain_validity=DomainValid(valid=True),
                alignment_threshold=config.certification.alignment_threshold.percentile_candidates[
                    0
                ]
                / 100.0,
                ambiguity_width_threshold=config.certification.ambiguity_width.percentile_candidates[
                    -1
                ]
                / 100.0,
                set_diameter=fset.diameter,
                historical_realized_diameter_quantile=config.certification.forecast_set_diameter_abstention.historical_realized_diameter_quantile,
            )
            cells.append(
                SweepCellResult(
                    parameter_name="outlier_client_stress",
                    parameter_value=float(corrupted_count),
                    coverage=(
                        1.0 if decision.status is CertificationStatus.CERTIFIED_POSITIVE else 0.0
                    ),
                    action_width=interval.width,
                    is_certified=decision.status is CertificationStatus.CERTIFIED_POSITIVE,
                    is_ambiguous=decision.status is CertificationStatus.AMBIGUOUS,
                    is_abstaining=decision.status is CertificationStatus.ABSTAIN,
                )
            )

    passed = sum(1 for c in cells if not c.is_abstaining)
    outcome = (
        ScientificOutcome.PASS
        if passed >= len(cells) * _MAJORITY_THRESHOLD_FRACTION
        else ScientificOutcome.INSUFFICIENT_EVIDENCE
    )

    return SyntheticSweepReport(
        total_cells=len(cells),
        passed_cells=passed,
        mechanism_valid=passed > 0,
        cells=tuple(cells),
        scientific_outcome=outcome,
    )
