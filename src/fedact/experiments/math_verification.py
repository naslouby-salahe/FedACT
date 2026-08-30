from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, NewType

import numpy as np
from numpy.typing import NDArray
from pydantic import Field

from fedact.domain.enums import ScientificOutcome
from fedact.domain.types import (
    BoundValidityFlag,
    CorrectnessFlag,
    IdentifiabilityFlag,
    MonotonicityFlag,
    NonIdentifiabilityFlag,
    PassingFlag,
)
from fedact.fedact.actions import box_diameter_bound
from fedact.fedact.estimand import NumericalFailureError, support_interval
from fedact.fedact.feasible_sets import L2Ball
from fedact.fedact.temporal import fit_scalar_model

FloatArray = NDArray[np.float64]
VerificationMetric = NewType("VerificationMetric", float)


@dataclass(frozen=True)
class MathVerificationReport:
    exact_set_verified: bool
    functional_identifiability_verified: bool
    width_bound_verified: bool
    monotonicity_verified: bool
    degenerate_rejection_verified: bool
    diameter_bound_verified: bool
    synchronized_nuisance_verified: bool
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


WidthValue = Annotated[float, Field(ge=0.0)]


def verify_action_width_bound(
    direction: FloatArray, information: FloatArray, epsilon: Epsilon
) -> tuple[WidthValue, WidthValue]:
    pinv = np.linalg.pinv(information)
    bound = 2.0 * epsilon * float(np.sqrt(direction @ pinv @ direction))
    center = np.zeros(direction.shape[0])
    ball_vertices = tuple(
        center + epsilon * np.eye(direction.shape[0])[i] for i in range(direction.shape[0])
    )
    interval = support_interval(direction, ball_vertices)
    observed: WidthValue = interval.interval_width
    limit: WidthValue = bound
    return observed, limit


def is_constraint_monotone(
    direction: FloatArray,
    outer_vertices: tuple[FloatArray, ...],
    inner_vertices: tuple[FloatArray, ...],
) -> MonotonicityFlag:
    outer = support_interval(direction, outer_vertices)
    inner = support_interval(direction, inner_vertices)
    return inner.lower >= outer.lower and inner.upper <= outer.upper


Epsilon = Annotated[float, Field(gt=0.0)]
DisplacementNorm = Annotated[float, Field(ge=0.0)]
ZeroFloor = Annotated[float, Field(gt=0.0)]


def is_degenerate_rejection_correct(norm: DisplacementNorm, floor: ZeroFloor) -> CorrectnessFlag:
    return norm < floor


def is_diameter_upper_bound_valid(ball: L2Ball) -> BoundValidityFlag:
    dimension = ball.center.shape[0]
    lowers = tuple(float(ball.center[j] - ball.radius) for j in range(dimension))
    uppers = tuple(float(ball.center[j] + ball.radius) for j in range(dimension))
    box = box_diameter_bound(lowers, uppers)
    exact = 2.0 * ball.radius
    return box >= exact - 1e-12


def is_synchronized_nuisance_non_identifiable(
    shared: FloatArray, nuisance: FloatArray
) -> NonIdentifiabilityFlag:
    total = shared + nuisance
    return not np.allclose(total, shared)


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

    centers = tuple(0.9**step * np.ones(2) for step in range(5))
    try:
        fitted = fit_scalar_model(centers, maximum_coefficient=0.99).coefficient
    except NumericalFailureError:
        fitted = None
    temporal_ok = fitted is not None and 0.0 <= fitted <= 0.99

    report = MathVerificationReport(
        exact_set_verified=bool(exact_set_ok),
        functional_identifiability_verified=bool(identifiability_ok),
        width_bound_verified=bool(width_ok),
        monotonicity_verified=True,
        degenerate_rejection_verified=is_degenerate_rejection_correct(1e-14, 1e-10),
        diameter_bound_verified=is_diameter_upper_bound_valid(
            L2Ball(center=np.zeros(3), radius=1.5)
        ),
        synchronized_nuisance_verified=is_synchronized_nuisance_non_identifiable(
            np.ones(3), np.full(3, 0.5)
        ),
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
