from __future__ import annotations

import numpy as np

from fedact.baselines.federation import (
    centralized_pooled_comparator,
    local_only_comparator,
)


def test_federation_comparators() -> None:
    c1 = np.array([1.0, 0.0])
    c2 = np.array([0.0, 1.0])
    pooled = centralized_pooled_comparator((c1, c2))
    assert np.allclose(pooled.aggregate_shift, np.array([0.5, 0.5]))

    local = local_only_comparator(c1)
    assert np.allclose(local.aggregate_shift, c1)
