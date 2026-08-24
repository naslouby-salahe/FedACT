from __future__ import annotations

from dataclasses import dataclass

from fedact.domain.enums import ScientificOutcome
from fedact.domain.types import DegradationValue, MetricRate, ValidationFlag


@dataclass(frozen=True)
class ScientificVerdictReport:
    primary_claim_confirmed: bool
    safety_guarantee_preserved: ValidationFlag
    overall_scientific_outcome: ScientificOutcome


def evaluate_scientific_verdicts(
    prospective_fnr: MetricRate,
    clean_fnr_degradation: DegradationValue,
    coverage: MetricRate,
) -> ScientificVerdictReport:
    claim = prospective_fnr < 0.15 and coverage >= 0.90
    safety = clean_fnr_degradation <= 2.0
    outcome = ScientificOutcome.PASS if (claim and safety) else ScientificOutcome.FAIL
    return ScientificVerdictReport(
        primary_claim_confirmed=claim,
        safety_guarantee_preserved=safety,
        overall_scientific_outcome=outcome,
    )
