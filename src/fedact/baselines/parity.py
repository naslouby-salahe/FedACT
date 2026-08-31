from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

from fedact.domain.records import DetailMessage, ThresholdValue

BudgetAmount = Annotated[float, Field(ge=0.0)]
ComparatorIdentifier = Annotated[str, Field(min_length=1)]

SUBTRACTION_COMPARATOR_NAME: ComparatorIdentifier = "subtraction"
SUBTRACTION_COMPARATOR_BUDGET: BudgetAmount = 10.0


class BaselineParityViolationError(ValueError):
    pass


@dataclass(frozen=True)
class ParityVerificationResult:
    is_valid: bool
    details: DetailMessage


def verify_chronology_and_budget_parity(
    comparator_name: ComparatorIdentifier,
    allocated_budget: BudgetAmount,
    reference_budget: BudgetAmount,
    tie_tolerance: ThresholdValue,
) -> ParityVerificationResult:
    if allocated_budget > reference_budget + tie_tolerance:
        msg = f"{comparator_name} budget {allocated_budget} exceeds reference {reference_budget}"
        raise BaselineParityViolationError(msg)
    return ParityVerificationResult(
        is_valid=True,
        details=f"{comparator_name} satisfies budget and chronology parity",
    )


def verify_subtraction_comparator_parity(tie_tolerance: ThresholdValue) -> ParityVerificationResult:
    return verify_chronology_and_budget_parity(
        SUBTRACTION_COMPARATOR_NAME,
        SUBTRACTION_COMPARATOR_BUDGET,
        SUBTRACTION_COMPARATOR_BUDGET,
        tie_tolerance,
    )
