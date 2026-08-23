from __future__ import annotations

import numpy as np

from fedact.experiments.math_verification import is_functionally_identifiable


def test_functional_identifiability_contract_orthogonal_decomposition() -> None:
    stacked = np.vstack([np.eye(4)[:2], np.zeros((2, 4))])
    q_identifiable = np.array([0.6, 0.8, 0.0, 0.0])
    q_unidentifiable = np.array([0.0, 0.0, 0.6, 0.8])
    assert is_functionally_identifiable(q_identifiable, stacked)
    assert not is_functionally_identifiable(q_unidentifiable, stacked)
