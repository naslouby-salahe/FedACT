from __future__ import annotations

from fedact.baselines.parity import verify_chronology_and_budget_parity


def test_baseline_fairness_parity_enforced() -> None:
    res = verify_chronology_and_budget_parity(
        "subtraction", allocated_budget=50.0, reference_budget=50.0
    )
    assert res.is_valid
