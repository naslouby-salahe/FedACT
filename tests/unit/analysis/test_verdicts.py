from __future__ import annotations

from fedact.analysis.verdicts import evaluate_scientific_verdicts
from fedact.config.loading import LoadedConfiguration
from fedact.domain.enums import ScientificOutcome


def test_evaluate_scientific_verdicts(production_configuration: LoadedConfiguration) -> None:
    res = evaluate_scientific_verdicts(
        prospective_fnr=0.08,
        clean_fnr_degradation=1.0,
        coverage=0.99,
        statistics_config=production_configuration.values.statistics,
        hardening_config=production_configuration.values.hardening,
    )
    assert res.primary_claim_confirmed
    assert res.safety_guarantee_preserved
    assert res.overall_scientific_outcome is ScientificOutcome.PASS
