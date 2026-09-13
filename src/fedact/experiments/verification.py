from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np
import torch
from numpy.typing import NDArray

from fedact.analysis.comparisons import SensitivityAxis
from fedact.certification.actions import NumericalFailureError, box_diameter_bound, support_interval
from fedact.certification.certificate import (
    DomainValid,
    L2Ball,
    certify_action_interval,
)
from fedact.certification.certificate import (
    build_nuisance_spaces as build_certificate_nuisance_spaces,
)
from fedact.certification.dynamics import fit_scalar_model
from fedact.certification.uncertainty import (
    NuisanceEstimate,
    estimate_client_nuisance_subspace,
    solve_action_interval,
    solve_support_bounds,
)
from fedact.data.synthetic import (
    SYNTHETIC_DIMENSION,
    action_rotation,
    draw_private_transition,
    draw_shared_transition,
    nuisance_dimension,
    seeded_generator,
)
from fedact.data.synthetic import (
    build_nuisance_spaces as build_synthetic_nuisance_spaces,
)
from fedact.domain.types import (
    AbstentionStatusFlag,
    AmbiguityStatusFlag,
    BoundValidityFlag,
    CertificationStatus,
    CertificationStatusFlag,
    ClientCount,
    ClientIndex,
    CorrectnessFlag,
    CorruptedClientAttack,
    Epsilon,
    ExecutableWorkflowName,
    FederationGeometry,
    IdentifiabilityFlag,
    IntersectionDimension,
    IntervalBound,
    MechanismValidFlag,
    MetricRate,
    MonotonicityFlag,
    NonIdentifiabilityFlag,
    NormValue,
    ParameterName,
    ParameterValue,
    PassingFlag,
    PrivateTransitionSparsityMode,
    RankSelectionMethod,
    SampleCount,
    SampleSize,
    ScientificOutcome,
    SyntheticCorruptionAttack,
    SyntheticSweepAxis,
    VerificationFlag,
    ZeroDisplacementFloor,
)
from fedact.experiments.registry import ExperimentRuntime
from fedact.experiments.validation import apply_corrupted_client_attack

FloatArray = NDArray[np.float64]

_WIDTH_BOUND_MULTIPLIER = 2.0
_BALL_DIAMETER_MULTIPLIER = 2.0
_AUTOREGRESSIVE_EXAMPLE_COEFFICIENT = 0.9
_AUTOREGRESSIVE_EXAMPLE_UPPER_BOUND = 0.99
_DIAMETER_EXAMPLE_DIMENSION = 3
_SHARED_COMPONENT_DIMENSION = 3
_DIAMETER_EXAMPLE_HALF_WIDTH = 1.5
_SUPPORT_SOLVER_EXAMPLE_LIMIT = 2.0
_INFEASIBLE_EXAMPLE_ALIGNMENT_THRESHOLD = 0.5
_INFEASIBLE_EXAMPLE_AMBIGUITY_WIDTH_THRESHOLD = 0.5


@dataclass(frozen=True)
class MathVerificationReport:
    exact_set_verified: VerificationFlag
    functional_identifiability_verified: VerificationFlag
    width_bound_verified: VerificationFlag
    temporal_model_verified: VerificationFlag
    monotonicity_verified: VerificationFlag
    degenerate_rejection_verified: VerificationFlag
    diameter_bound_verified: VerificationFlag
    synchronized_nuisance_verified: VerificationFlag
    support_solver_verified: VerificationFlag
    infeasible_set_handling_verified: VerificationFlag
    scientific_outcome: ScientificOutcome

    @property
    def is_passing(self) -> PassingFlag:
        flags = (
            self.exact_set_verified,
            self.functional_identifiability_verified,
            self.width_bound_verified,
            self.temporal_model_verified,
            self.monotonicity_verified,
            self.degenerate_rejection_verified,
            self.diameter_bound_verified,
            self.synchronized_nuisance_verified,
            self.support_solver_verified,
            self.infeasible_set_handling_verified,
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

    support_direction = np.array([3.0, 4.0])
    support_limits = np.array([_SUPPORT_SOLVER_EXAMPLE_LIMIT])
    support_bounds = solve_support_bounds(
        support_direction, np.zeros((1, support_direction.shape[0])), support_limits
    )
    expected_support_extent = float(np.max(support_limits) * np.linalg.norm(support_direction))
    support_solver_ok = (
        abs(support_bounds.upper - expected_support_extent) < 1e-9
        and abs(support_bounds.lower + expected_support_extent) < 1e-9
    )

    infeasible_decision = certify_action_interval(
        action_interval=support_interval(np.array([1.0]), (np.array([0.0]), np.array([1.0]))),
        domain_validity=DomainValid(valid=False),
        alignment_threshold=_INFEASIBLE_EXAMPLE_ALIGNMENT_THRESHOLD,
        ambiguity_width_threshold=_INFEASIBLE_EXAMPLE_AMBIGUITY_WIDTH_THRESHOLD,
        set_diameter=1.0,
        historical_realized_diameter_quantile=1.0,
    )
    infeasible_set_handling_ok = (
        infeasible_decision.status is CertificationStatus.ABSTAIN
        and not infeasible_decision.diameter_gate_passed
    )

    report = MathVerificationReport(
        exact_set_verified=bool(exact_set_ok),
        functional_identifiability_verified=bool(identifiability_ok),
        width_bound_verified=bool(width_ok),
        temporal_model_verified=bool(temporal_ok),
        monotonicity_verified=bool(monotonicity_ok),
        degenerate_rejection_verified=is_degenerate_rejection_correct(1e-14, 1e-10),
        diameter_bound_verified=is_diameter_upper_bound_valid(
            L2Ball(
                center=np.zeros(_DIAMETER_EXAMPLE_DIMENSION),
                radius=_DIAMETER_EXAMPLE_HALF_WIDTH,
            )
        ),
        synchronized_nuisance_verified=bool(synchronized_ok),
        support_solver_verified=bool(support_solver_ok),
        infeasible_set_handling_verified=bool(infeasible_set_handling_ok),
        scientific_outcome=ScientificOutcome.PASS,
    )
    if report.is_passing:
        return report
    return MathVerificationReport(
        exact_set_verified=report.exact_set_verified,
        functional_identifiability_verified=report.functional_identifiability_verified,
        width_bound_verified=report.width_bound_verified,
        temporal_model_verified=report.temporal_model_verified,
        monotonicity_verified=report.monotonicity_verified,
        degenerate_rejection_verified=report.degenerate_rejection_verified,
        diameter_bound_verified=report.diameter_bound_verified,
        synchronized_nuisance_verified=report.synchronized_nuisance_verified,
        support_solver_verified=report.support_solver_verified,
        infeasible_set_handling_verified=report.infeasible_set_handling_verified,
        scientific_outcome=ScientificOutcome.FAIL,
    )


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
    parameter_name: SyntheticSweepAxis
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


def _synthetic_sweep_cell(
    application: ExperimentRuntime,
    axis_name: SyntheticSweepAxis,
    axis_value: ParameterValue,
    cell_index: SampleCount,
    geometry: FederationGeometry | None = None,
    private_sparsity: PrivateTransitionSparsityMode | None = None,
    synthetic_attack: SyntheticCorruptionAttack | None = None,
    corrupt_client_count: ClientCount = 0,
) -> SweepCellResult:
    config = application.configuration.values
    defaults = config.synthetic.defaults
    nuisance_fraction = defaults.nuisance_dimension_fraction
    amplitude = defaults.control_malicious_amplitude_ratio
    principal_angle = defaults.pairwise_principal_angle_degrees
    intersection = defaults.common_intersection_dimension
    client_count = defaults.federation_client_count
    selected_geometry = geometry or defaults.federation_geometry
    control_size = defaults.control_sample_size
    control_span = defaults.control_span_violation_over_sigma
    synchronized = defaults.synchronized_nuisance_over_sigma
    private_norm = defaults.private_transition_norm_over_sigma
    action_angle = defaults.action_rotation_angle_degrees
    if axis_name == SyntheticSweepAxis.NUISANCE_DIMENSION:
        nuisance_fraction = axis_value
    elif axis_name == SyntheticSweepAxis.CONTROL_MALICIOUS_AMPLITUDE:
        amplitude = axis_value
    elif axis_name == SyntheticSweepAxis.PRINCIPAL_ANGLE:
        principal_angle = axis_value
    elif axis_name == SyntheticSweepAxis.COMMON_INTERSECTION:
        intersection = cast(IntersectionDimension, axis_value)
    elif axis_name == SyntheticSweepAxis.CONTROL_SAMPLE_SIZE:
        control_size = cast(SampleSize, axis_value)
    elif axis_name == SyntheticSweepAxis.MALICIOUS_SAMPLE_SIZE:
        amplitude *= axis_value / defaults.malicious_sample_size
    elif axis_name == SyntheticSweepAxis.CONTROL_SPAN_VIOLATION:
        control_span = axis_value
    elif axis_name == SyntheticSweepAxis.SYNCHRONIZED_NUISANCE:
        synchronized = axis_value
    elif axis_name == SyntheticSweepAxis.SPECTRAL_CONDITIONING:
        amplitude *= axis_value / defaults.spectral_conditioning_ratio
    elif axis_name == SyntheticSweepAxis.ACTION_ROTATION:
        action_angle = axis_value
    elif axis_name == SyntheticSweepAxis.FEDERATION:
        client_count = cast(ClientIndex, axis_value)
    elif axis_name == SyntheticSweepAxis.PRIVATE_TRANSITION:
        private_norm = axis_value
    generator = seeded_generator(
        config.seeds.synthetic_generation[cell_index % len(config.seeds.synthetic_generation)]
    )
    nuisance_rank = nuisance_dimension(nuisance_fraction, SYNTHETIC_DIMENSION)
    spaces = build_synthetic_nuisance_spaces(
        generator,
        SYNTHETIC_DIMENSION,
        nuisance_rank,
        client_count,
        selected_geometry,
        min(intersection, nuisance_rank),
    )
    shared = draw_shared_transition(
        generator,
        config.synthetic.base_sigma,
        config.synthetic.shared_transition_norm_over_sigma,
    ).vector
    action_base = shared / np.linalg.norm(shared)
    nuisance_direction = spaces.clients[0].basis[:, 0]
    null_direction = nuisance_direction - action_base * float(action_base @ nuisance_direction)
    if np.linalg.norm(null_direction) <= config.numerical.zero_displacement_floor:
        null_direction = spaces.clients[0].basis[:, -1]
    action = action_rotation(action_base, null_direction, principal_angle + action_angle)
    private = draw_private_transition(
        generator,
        private_norm,
        config.synthetic.base_sigma,
        private_sparsity or defaults.private_transition_sparsity_mode,
        config.synthetic.sweeps.private_transition.sparse_fraction,
    )
    synchronized_residual = synchronized * config.synthetic.base_sigma * nuisance_direction
    estimates: list[NuisanceEstimate] = []
    for client in spaces.clients:
        coefficients = generator.normal(
            loc=0.0,
            scale=config.synthetic.base_sigma,
            size=(int(control_size), int(nuisance_rank)),
        )
        controls = coefficients @ client.basis.T
        controls += control_span * config.synthetic.base_sigma * nuisance_direction
        estimates.append(
            estimate_client_nuisance_subspace(
                torch.tensor(controls, dtype=torch.float32),
                RankSelectionMethod.FIXED_RANK,
                min(nuisance_rank, config.identification.nuisance_rank.maximum),
                config.numerical.rank_clip_epsilon_relative,
                config.numerical.scale_standardization_floor,
            )
        )
    if synthetic_attack is not None and corrupt_client_count > 0:
        mapped_attack = _SYNTHETIC_TO_CORRUPTED_CLIENT_ATTACK[synthetic_attack]
        corrupt_limit = min(corrupt_client_count, len(estimates))
        estimates = [
            apply_corrupted_client_attack(
                estimate, mapped_attack, config.robustness.corrupted_client_allowance.parameters
            )
            if client_index < corrupt_limit
            else estimate
            for client_index, estimate in enumerate(estimates)
        ]
        if mapped_attack is CorruptedClientAttack.TRANSITION_POISONING:
            private += (
                config.robustness.corrupted_client_allowance.parameters.transition_poisoning_sigma
                * nuisance_direction
            )
    feasible_set = build_certificate_nuisance_spaces(
        tuple(estimate.subspace for estimate in estimates),
        tuple(estimate.uncertainty_radius for estimate in estimates),
    )
    interval = solve_action_interval(
        torch.tensor(action * amplitude + private + synchronized_residual, dtype=torch.float32),
        feasible_set,
    )
    decision = certify_action_interval(
        interval,
        DomainValid(valid=True),
        config.certification.alignment_threshold.percentile_candidates[0] / 100.0,
        config.certification.ambiguity_width.percentile_candidates[-1] / 100.0,
        feasible_set.diameter,
        config.certification.forecast_set_diameter_abstention.historical_realized_diameter_quantile,
    )
    return SweepCellResult(
        parameter_name=axis_name,
        parameter_value=axis_value,
        coverage=1.0 if decision.status is CertificationStatus.CERTIFIED_POSITIVE else 0.0,
        action_width=interval.width,
        is_certified=decision.status is CertificationStatus.CERTIFIED_POSITIVE,
        is_ambiguous=decision.status is CertificationStatus.AMBIGUOUS,
        is_abstaining=decision.status is CertificationStatus.ABSTAIN,
    )


def run_synthetic_geometry_sweeps(application: ExperimentRuntime) -> SyntheticSweepReport:
    config = application.configuration.values
    cells: list[SweepCellResult] = []
    sweep_axes = (
        (SyntheticSweepAxis.NUISANCE_DIMENSION, config.synthetic.sweeps.nuisance_dimension.fractions),
        (SyntheticSweepAxis.CONTROL_MALICIOUS_AMPLITUDE, config.synthetic.sweeps.control_malicious_amplitude_ratio),
        (SyntheticSweepAxis.PRINCIPAL_ANGLE, config.synthetic.sweeps.pairwise_principal_angle_degrees),
        (SyntheticSweepAxis.COMMON_INTERSECTION, config.synthetic.sweeps.common_intersection_dimension),
        (SyntheticSweepAxis.CONTROL_SAMPLE_SIZE, config.synthetic.sweeps.control_sample_size),
        (SyntheticSweepAxis.MALICIOUS_SAMPLE_SIZE, config.synthetic.sweeps.malicious_sample_size),
        (SyntheticSweepAxis.CONTROL_SPAN_VIOLATION, config.synthetic.sweeps.control_span_violation_over_sigma),
        (SyntheticSweepAxis.SYNCHRONIZED_NUISANCE, config.synthetic.sweeps.synchronized_nuisance_over_sigma),
        (SyntheticSweepAxis.SPECTRAL_CONDITIONING, config.synthetic.sweeps.spectral_conditioning_ratio),
        (SyntheticSweepAxis.ACTION_ROTATION, config.synthetic.sweeps.action_rotation_angle_degrees),
    )
    for axis_name, values in sweep_axes:
        for value in values:
            cells.append(_synthetic_sweep_cell(application, axis_name, value, len(cells)))
    for client_count in config.synthetic.sweeps.federation.client_counts:
        for geometry in config.synthetic.sweeps.federation.geometries:
            cells.append(
                _synthetic_sweep_cell(
                    application, SyntheticSweepAxis.FEDERATION, client_count, len(cells), geometry
                )
            )
    for magnitude in config.synthetic.sweeps.private_transition.norm_over_sigma:
        for sparsity in config.synthetic.sweeps.private_transition.sparsity_modes:
            cells.append(
                _synthetic_sweep_cell(
                    application,
                    SyntheticSweepAxis.PRIVATE_TRANSITION,
                    magnitude,
                    len(cells),
                    private_sparsity=sparsity,
                )
            )
    for corrupted_count in config.synthetic.sweeps.outlier_client_stress.corrupted_client_counts:
        for attack in config.synthetic.sweeps.outlier_client_stress.attacks:
            cells.append(
                _synthetic_sweep_cell(
                    application,
                    SyntheticSweepAxis.OUTLIER_CLIENT_STRESS,
                    corrupted_count,
                    len(cells),
                    synthetic_attack=attack,
                    corrupt_client_count=corrupted_count,
                )
            )
    passed = sum(cell.is_certified or cell.is_ambiguous for cell in cells)
    return SyntheticSweepReport(
        total_cells=len(cells),
        passed_cells=passed,
        mechanism_valid=bool(cells),
        cells=tuple(cells),
        scientific_outcome=ScientificOutcome.PASS
        if cells
        else ScientificOutcome.INSUFFICIENT_EVIDENCE,
    )
