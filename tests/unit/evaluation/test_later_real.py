from __future__ import annotations

import numpy as np

from fedact.evaluation.later_real import build_later_real_proxy


def test_build_later_real_proxy() -> None:
    before = np.zeros((10, 64))
    after = np.ones((10, 64))
    proxy = build_later_real_proxy(before, after)
    assert np.allclose(proxy.observed_transition, 1.0)
    assert proxy.sample_count == 10
