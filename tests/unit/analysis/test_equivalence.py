from __future__ import annotations

from fedact.analysis.equivalence import tost_equivalence


def test_tost_equivalence() -> None:
    t = [0.10, 0.10, 0.10]
    c = [0.10, 0.10, 0.10]
    res = tost_equivalence(t, c, equivalence_margin=0.05)
    assert res.is_equivalent
