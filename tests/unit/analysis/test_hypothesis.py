from __future__ import annotations

from fedact.analysis.hypothesis import paired_t_test


def test_paired_t_test() -> None:
    treatment = [0.1, 0.2, 0.15, 0.12]
    control = [0.4, 0.5, 0.45, 0.42]
    res = paired_t_test(treatment, control)
    assert res.is_significant
