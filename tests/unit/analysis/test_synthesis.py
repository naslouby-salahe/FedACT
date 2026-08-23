from __future__ import annotations

from fedact.analysis.synthesis import synthesize_treatment_effects


def test_synthesize_treatment_effects() -> None:
    t = [0.08, 0.09]
    b = [0.30, 0.32]
    res = synthesize_treatment_effects(t, b)
    assert res.cohens_d < 0.0
