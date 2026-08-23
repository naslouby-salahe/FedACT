from __future__ import annotations

from fedact.analysis.correction import benjamini_hochberg_correction


def test_benjamini_hochberg_correction() -> None:
    p_vals = [0.01, 0.04, 0.03]
    adj = benjamini_hochberg_correction(p_vals)
    assert len(adj) == 3
    assert all(p <= 1.0 for p in adj)
