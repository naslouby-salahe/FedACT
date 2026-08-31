from __future__ import annotations

from fedact.config.loading import LoadedConfiguration
from fedact.domain.enums import ScientificOutcome
from fedact.experiments.client_selection import run_communication_limited_client_selection


def test_run_communication_limited_client_selection(
    production_configuration: LoadedConfiguration,
) -> None:
    report = run_communication_limited_client_selection(production_configuration.values)
    assert report.budget_fractions_tested > 0
    assert report.scientific_outcome is ScientificOutcome.PASS
