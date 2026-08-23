from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated

import numpy as np
from pydantic import Field

Threshold = Annotated[float, Field()]
WidthLimit = Annotated[float, Field(gt=0.0)]
DiameterValue = Annotated[float, Field(ge=0.0)]
StabilityFraction = Annotated[float, Field(gt=0.0, le=1.0)]


@dataclass(frozen=True)
class DomainValid:
    valid: bool


class CertificateState(StrEnum):
    CERTIFIED = "CERTIFIED"
    POSITIVE = "POSITIVELY_IDENTIFIED"
    NEGATIVE = "NEGATIVELY_IDENTIFIED"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass(frozen=True)
class CertificateDecision:
    state: CertificateState
    leave_one_client_out_note: str | None = None


def decide(
    lower: Threshold,
    upper: Threshold,
    tau_align: Threshold,
    tau_amb: WidthLimit,
    domain_valid: DomainValid,
) -> CertificateDecision:
    if not domain_valid:
        return CertificateDecision(state=CertificateState.NEGATIVE)
    if lower >= tau_align and (upper - lower) <= tau_amb:
        return CertificateDecision(state=CertificateState.CERTIFIED)
    if upper < tau_align:
        return CertificateDecision(state=CertificateState.NEGATIVE)
    return CertificateDecision(state=CertificateState.AMBIGUOUS)


def is_forecast_set_within_gate(
    diameter_bound: DiameterValue, historical_quantile_value: DiameterValue
) -> bool:
    return diameter_bound <= historical_quantile_value


def leave_one_client_out_stability(
    decisions: tuple[bool, ...], minimum_unchanged_fraction: StabilityFraction
) -> tuple[bool, int]:
    total = len(decisions)
    unchanged = sum(1 for decision in decisions if decision)
    required = int(np.ceil(minimum_unchanged_fraction * total))
    return unchanged >= required, required


def downgrade_dominant_single_client(state: CertificateState) -> CertificateState:
    if state is CertificateState.CERTIFIED:
        return CertificateState.AMBIGUOUS
    return state
