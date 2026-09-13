from __future__ import annotations

import numpy as np
import pytest
import torch

from fedact.certification.certificate import (
    ClientConstraint,
    FeasibleSet,
    L2Ball,
    build_nuisance_spaces,
    chebyshev_center,
    compute_chebyshev_center,
    is_constraint_satisfied,
    minimum_uniform_inflation,
)
from fedact.domain.types import FederationGeometry

DIAMETER_DOUBLING_FACTOR = 2.0
X_AXIS_PROJECTOR = np.array([[1.0, 0.0], [0.0, 0.0]], dtype=np.float64)
CENTER = np.array([0.0, 0.0], dtype=np.float64)
X_AXIS_SPAN = np.array([[1.0], [0.0]], dtype=np.float64)


def _constraint(
    *,
    projector: np.ndarray | None = None,
    subspace: torch.Tensor | np.ndarray | None = None,
    radius: float = 1.0,
) -> ClientConstraint:
    return ClientConstraint(
        client_index=0,
        uncertainty_radius=radius,
        beta=radius,
        subspace=subspace,
        projector=projector,
    )


def _feasible_set(
    nuisance_subspaces: tuple[torch.Tensor, ...] | None = None,
    uncertainty_radii: tuple[float, ...] = (0.5,),
    diameter: float = 1.0,
    center: np.ndarray | torch.Tensor | None = None,
    plausibility_ball: L2Ball | None = None,
) -> FeasibleSet:
    return FeasibleSet(
        nuisance_subspaces=(
            (torch.zeros((2, 2)),) if nuisance_subspaces is None else nuisance_subspaces
        ),
        uncertainty_radii=uncertainty_radii,
        diameter=diameter,
        center=center,
        plausibility_ball=plausibility_ball,
    )


def test_chebyshev_center_of_a_point_cloud_is_the_mean_with_the_worst_radius() -> None:
    points = np.array([[0.0, 0.0], [2.0, 0.0], [1.0, 0.0]], dtype=np.float64)
    result = chebyshev_center(points)
    assert np.allclose(result.center, np.array([1.0, 0.0]))
    assert result.radius == pytest.approx(1.0)


def test_chebyshev_center_rejects_an_empty_point_cloud() -> None:
    with pytest.raises(ValueError, match="at least one point"):
        chebyshev_center(np.zeros((0, 2), dtype=np.float64))


def test_chebyshev_center_of_a_feasible_set_halves_its_diameter() -> None:
    result = chebyshev_center(_feasible_set(center=CENTER, diameter=4.0))
    assert np.allclose(result.center, CENTER)
    assert result.radius == pytest.approx(4.0 / DIAMETER_DOUBLING_FACTOR)


def test_feasible_set_without_a_center_falls_back_to_its_plausibility_ball() -> None:
    ball = L2Ball(center=np.array([3.0, 4.0], dtype=np.float64), radius=1.0)
    result = chebyshev_center(_feasible_set(plausibility_ball=ball, diameter=2.0))
    assert np.allclose(result.center, np.array([3.0, 4.0]))


def test_feasible_set_without_any_center_uses_the_nuisance_dimension() -> None:
    result = chebyshev_center(_feasible_set(nuisance_subspaces=(torch.zeros((3, 3)),)))
    assert result.center.shape == (3,)
    assert np.allclose(result.center, np.zeros(3))


def test_chebyshev_center_rejects_an_empty_constraint_sequence() -> None:
    with pytest.raises(ValueError, match="at least one constraint"):
        chebyshev_center([])


def test_chebyshev_center_of_constraints_uses_their_subspace_dimension() -> None:
    result = chebyshev_center([_constraint(subspace=torch.zeros((3, 3)), radius=0.25)])
    assert result.center.shape == (3,)
    assert result.radius == pytest.approx(0.25)


def test_minimum_uniform_inflation_requires_a_positive_vertex_budget() -> None:
    with pytest.raises(ValueError, match="positive vertex budget"):
        minimum_uniform_inflation(vertices=0)


def test_minimum_uniform_inflation_requires_a_ball_and_constraints() -> None:
    ball = L2Ball(center=CENTER, radius=1.0)
    with pytest.raises(ValueError, match="plausibility ball and client constraints"):
        minimum_uniform_inflation(ball, vertices=8)


def test_minimum_uniform_inflation_is_never_below_one() -> None:
    ball = L2Ball(center=CENTER, radius=1.0)
    inflation = minimum_uniform_inflation(
        ball, [_constraint(projector=X_AXIS_PROJECTOR)], vertices=8
    )
    assert inflation >= 1.0


def test_minimum_uniform_inflation_skips_constraints_without_a_projector() -> None:
    ball = L2Ball(center=CENTER, radius=1.0)
    inflation = minimum_uniform_inflation(ball, [_constraint()], vertices=8)
    assert inflation == 1.0


def test_build_nuisance_spaces_rejects_mismatched_radii() -> None:
    with pytest.raises(ValueError, match="matching uncertainty radius"):
        build_nuisance_spaces((torch.zeros((2, 2)),), ())


def test_build_nuisance_spaces_requires_at_least_one_subspace() -> None:
    with pytest.raises(ValueError, match="requires client nuisance subspaces"):
        build_nuisance_spaces((), ())


def test_build_nuisance_spaces_doubles_the_total_uncertainty() -> None:
    feasible_set = build_nuisance_spaces(
        (torch.zeros((2, 2)), torch.zeros((2, 2))),
        (0.25, 0.75),
        FederationGeometry.COMPLEMENTARY,
    )
    assert feasible_set.diameter == pytest.approx(DIAMETER_DOUBLING_FACTOR * 1.0)
    assert len(feasible_set) == 0


def test_compute_chebyshev_center_prefers_an_explicit_array_center() -> None:
    computed = compute_chebyshev_center(_feasible_set(center=CENTER))
    assert isinstance(computed, torch.Tensor)
    assert torch.allclose(computed, torch.tensor(CENTER, dtype=torch.float32))


def test_compute_chebyshev_center_passes_a_tensor_center_through() -> None:
    tensor_center = torch.tensor([1.0, 2.0])
    assert compute_chebyshev_center(_feasible_set(center=tensor_center)) is tensor_center


def test_compute_chebyshev_center_requires_a_center_or_subspace() -> None:
    with pytest.raises(ValueError, match="requires nuisance subspaces or an explicit center"):
        compute_chebyshev_center(_feasible_set(nuisance_subspaces=()))


def test_compute_chebyshev_center_uses_the_subspace_dimension() -> None:
    computed = compute_chebyshev_center(_feasible_set(nuisance_subspaces=(torch.zeros((4, 4)),)))
    assert computed.shape == (4,)


def test_projected_constraint_is_satisfied_only_near_the_projection() -> None:
    constraint = _constraint(projector=X_AXIS_PROJECTOR, radius=0.1)
    assert is_constraint_satisfied(constraint, np.array([1.0, 0.0])) is True
    assert is_constraint_satisfied(constraint, np.array([0.0, 1.0])) is False


def test_subspace_constraint_residual_gates_satisfaction() -> None:
    constraint = _constraint(subspace=torch.tensor(X_AXIS_SPAN, dtype=torch.float64), radius=0.1)
    assert is_constraint_satisfied(constraint, np.array([1.0, 0.0])) is True
    assert is_constraint_satisfied(constraint, np.array([0.0, 2.0])) is False


def test_constraint_without_a_projector_or_subspace_is_unconstrained() -> None:
    assert is_constraint_satisfied(_constraint(), np.array([9.0, 9.0])) is True


def test_l2_ball_containment_respects_the_tolerance() -> None:
    ball = L2Ball(center=CENTER, radius=1.0)
    assert ball.is_containing(np.array([1.0, 0.0]), 0.0) is True
    assert ball.is_containing(np.array([1.5, 0.0]), 0.0) is False
    assert ball.is_containing(np.array([1.5, 0.0]), 0.5) is True
