from __future__ import annotations

import numpy as np
import pytest

from fedact.core.uncertainty import (
    client_radius,
    sampling_uncertainty_quantile,
    standardized_subspace_term,
    subspace_uncertainty,
)


def test_sampling_uncertainty_quantile_matches_empirical_quantile() -> None:
    norms = tuple(float(x) for x in range(101))
    quantile = sampling_uncertainty_quantile(norms, 0.1)
    assert quantile == pytest.approx(90.0)


def test_standardized_subspace_term_uses_sqrt_chi2() -> None:
    term = standardized_subspace_term(
        subspace_deviation=0.5, amplitude=1.0, smallest_eigenvalue=4.0
    )
    assert term == pytest.approx(0.25)


def test_subspace_uncertainty_combines_terms() -> None:
    proj1 = np.eye(3)
    proj2 = np.eye(3) + 0.1
    ref = np.eye(3)
    unc = subspace_uncertainty((proj1, proj2), ref, alpha=0.1)
    assert unc >= 0.0


def test_client_radius_sums_all_budget_terms() -> None:
    radius = client_radius(
        sampling=1.0,
        subspace=0.5,
        control_span=0.1,
        private_allowance=0.2,
    )
    assert radius == pytest.approx(1.8)
