from __future__ import annotations

import numpy as np

from fedact.baselines.security import (
    random_mutation_baseline,
    reactive_adaptation_baseline,
    static_security_baseline,
)


def test_security_baselines() -> None:
    static = static_security_baseline(dimension=64)
    assert np.allclose(static.predicted_shift, 0.0)

    rand = random_mutation_baseline(dimension=64, seed=2026)
    assert rand.predicted_shift.shape == (64,)

    recent = np.ones(64)
    react = reactive_adaptation_baseline(recent)
    assert np.allclose(react.predicted_shift, recent)
