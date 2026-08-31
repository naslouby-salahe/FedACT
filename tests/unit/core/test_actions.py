from __future__ import annotations

import numpy as np
import pytest

from fedact.core.actions import (
    action_support_bounds,
    box_diameter_bound,
    displace_sample_representation,
    evaluate_displacement,
)


def test_evaluate_displacement_rejects_sub_floor_norm() -> None:
    res = evaluate_displacement(np.zeros(4), np.zeros(4), zero_displacement_floor=1e-10)
    assert res.rejected_as_degenerate


def test_action_support_bounds_calls_solver() -> None:
    direction = np.array([0.0, 1.0])
    lower_vertex = np.array([0.0, -1.5])
    upper_vertex = np.array([0.0, 1.5])
    res = action_support_bounds(direction, (lower_vertex, upper_vertex))
    assert res.lower == pytest.approx(-1.5, abs=1e-4)
    assert res.upper == pytest.approx(1.5, abs=1e-4)


def test_box_diameter_bound() -> None:
    lowers = (-1.0, -2.0)
    uppers = (1.0, 2.0)
    diameter = box_diameter_bound(lowers, uppers)
    assert diameter == pytest.approx(np.sqrt(2.0**2 + 4.0**2))


def test_displace_sample_representation_rejects_sub_floor_norm() -> None:
    import torch

    source = torch.zeros(4)
    delta = torch.zeros(4)
    res = displace_sample_representation(source, delta, norm_floor=1e-6)
    assert res.rejected_as_degenerate


def test_displace_sample_representation_applies_nondegenerate_delta() -> None:
    import torch

    source = torch.zeros(4)
    delta = torch.ones(4)
    res = displace_sample_representation(source, delta, norm_floor=1e-6)
    assert not res.rejected_as_degenerate
    assert isinstance(res.displacement_vector, torch.Tensor)
    assert torch.allclose(res.displacement_vector, delta)
