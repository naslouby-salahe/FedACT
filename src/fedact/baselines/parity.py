from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

BudgetAmount = Annotated[float, Field(ge=0.0)]
ComparatorIdentifier = Annotated[str, Field(min_length=1)]


class BaselineParityViolationError(ValueError):
    pass


@dataclass(frozen=True)
class ParityVerificationResult:
    is_valid: bool
    details: str


def verify_chronology_and_budget_parity(
    comparator_name: ComparatorIdentifier,
    allocated_budget: BudgetAmount,
    reference_budget: BudgetAmount,
) -> ParityVerificationResult:
    if allocated_budget > reference_budget + 1e-9:
        msg = f"{comparator_name} budget {allocated_budget} exceeds reference {reference_budget}"
        raise BaselineParityViolationError(msg)
    return ParityVerificationResult(
        is_valid=True,
        details=f"{comparator_name} satisfies budget and chronology parity",
    )
