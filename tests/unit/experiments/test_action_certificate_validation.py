from __future__ import annotations

from fedact.config.loading import LoadedConfiguration
from fedact.domain.enums import ScientificOutcome
from fedact.experiments.action_certificate_validation import run_action_certificate_validation


def test_run_action_certificate_validation(production_configuration: LoadedConfiguration) -> None:
    report = run_action_certificate_validation(production_configuration.values)
    assert report.total_actions > 0
    assert report.scientific_outcome is ScientificOutcome.PASS
