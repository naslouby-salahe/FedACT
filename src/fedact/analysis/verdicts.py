from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

from fedact.domain.enums import ScientificOutcome

FnrThreshold = Annotated[float, Field(ge=0.0, le=1.0)]
DegradationLimit = Annotated[float, Field(ge=0.0)]
CoverageBound = Annotated[float, Field(ge=0.0, le=1.0)]


@dataclass(frozen=True)
class ScientificVerdictReport:
    primary_claim_confirmed: bool
    safety_guarantee_preserved: bool
    overall_scientific_outcome: ScientificOutcome


def evaluate_scientific_verdicts(
    prospective_fnr: FnrThreshold,
    clean_fnr_degradation: DegradationLimit,
    coverage: CoverageBound,
) -> ScientificVerdictReport:
    claim = prospective_fnr < 0.15 and coverage >= 0.90
    safety = clean_fnr_degradation <= 2.0
    outcome = ScientificOutcome.PASS if (claim and safety) else ScientificOutcome.FAIL
    return ScientificVerdictReport(
        primary_claim_confirmed=claim,
        safety_guarantee_preserved=safety,
        overall_scientific_outcome=outcome,
    )
