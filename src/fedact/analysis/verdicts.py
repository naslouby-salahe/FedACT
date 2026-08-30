from __future__ import annotations

from dataclasses import dataclass

from fedact.config.models import HardeningConfig, StatisticsConfig
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
    statistics_config: StatisticsConfig,
    hardening_config: HardeningConfig,
) -> ScientificVerdictReport:
    max_coverage_deficit = (
        statistics_config.minimum_material_effects.maximum_coverage_deficit_absolute
    )
    claim = prospective_fnr < 0.15 and coverage >= (1.0 - max_coverage_deficit)
    safety = (
        clean_fnr_degradation
        <= hardening_config.weight.maximum_clean_fnr_degradation_percentage_points
    )
    outcome = ScientificOutcome.PASS if (claim and safety) else ScientificOutcome.FAIL
    return ScientificVerdictReport(
        primary_claim_confirmed=claim,
        safety_guarantee_preserved=safety,
        overall_scientific_outcome=outcome,
    )
