from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, NewType, cast

import cvxpy as cp
import numpy as np
from numpy.typing import NDArray
from pydantic import Field
from scipy import sparse

FloatArray = NDArray[np.float64]
SolverOutcome = NewType("SolverOutcome", str)

OPTIMAL_INACCURATE_STATES = frozenset({"optimal_inaccurate"})


@dataclass(frozen=True)
class SolverOptions:
    reltol: float
    abstol: float
    feastol: float
    max_iters: int


@dataclass(frozen=True)
class SolverToleranceSettings:
    relative_tolerance: Annotated[float, Field(gt=0.0)]
    absolute_tolerance: Annotated[float, Field(gt=0.0)]
    duality_gap_tolerance: Annotated[float, Field(gt=0.0)]
    maximum_iterations: Annotated[int, Field(ge=1)]

    def solver_options(self) -> SolverOptions:
        return SolverOptions(
            reltol=self.relative_tolerance,
            abstol=self.absolute_tolerance,
            feastol=self.duality_gap_tolerance,
            max_iters=self.maximum_iterations,
        )


def _terminal_state(status: str) -> SolverOutcome:
    if status == cp.OPTIMAL:
        return SolverOutcome("optimal")
    if status in OPTIMAL_INACCURATE_STATES:
        raise RuntimeError(f"unresolved inaccurate solver terminal state: {status}")
    if status == cp.INFEASIBLE:
        return SolverOutcome("infeasible")
    raise RuntimeError(f"solver failed with status {status}")


def solve_support_bounds(
    direction: FloatArray,
    constraint_coefficients: FloatArray,
    constraint_limits: FloatArray,
    settings: SolverToleranceSettings,
) -> tuple[float, float]:
    variable = cp.Variable(direction.shape[0])
    inequality = cast(
        "list[cp.Constraint]",
        [sparse.csc_matrix(constraint_coefficients) @ variable <= constraint_limits],
    )
    options = settings.solver_options()
    problem_min = cp.Problem(cp.Minimize(direction @ variable), inequality)
    problem_min.solve(solver=cp.ECOS, warm_start=False, **vars(options))
    _terminal_state(str(problem_min.status))
    lower_value = float(cast(float, problem_min.value))
    problem_max = cp.Problem(cp.Maximize(direction @ variable), inequality)
    problem_max.solve(solver=cp.ECOS, warm_start=False, **vars(options))
    _terminal_state(str(problem_max.status))
    upper_value = float(cast(float, problem_max.value))
    return lower_value, upper_value


def is_feasible_under_constraints(
    constraint_coefficients: FloatArray,
    constraint_limits: FloatArray,
    settings: SolverToleranceSettings,
) -> bool:
    variable = cp.Variable(constraint_coefficients.shape[1])
    inequality = cast(
        "list[cp.Constraint]",
        [sparse.csc_matrix(constraint_coefficients) @ variable <= constraint_limits],
    )
    problem = cp.Problem(cp.Minimize(0), inequality)
    problem.solve(solver=cp.ECOS, warm_start=False, **vars(settings.solver_options()))
    outcome = _terminal_state(str(problem.status))
    return outcome == SolverOutcome("optimal")
