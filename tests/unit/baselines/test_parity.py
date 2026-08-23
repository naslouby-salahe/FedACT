from __future__ import annotations

import pytest

from fedact.baselines.parity import (
    BaselineParityViolationError,
    verify_chronology_and_budget_parity,
)


def test_parity_verification_accepts_valid_budget() -> None:
    res = verify_chronology_and_budget_parity(
        "subtraction", allocated_budget=10.0, reference_budget=10.0
    )
    assert res.is_valid


def test_parity_verification_rejects_exceeded_budget() -> None:
    with pytest.raises(BaselineParityViolationError):
        verify_chronology_and_budget_parity(
            "subtraction", allocated_budget=15.0, reference_budget=10.0
        )
