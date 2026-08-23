from __future__ import annotations

from fedact.config.loading import LoadedConfiguration
from fedact.domain.enums import ScientificOutcome
from fedact.experiments.ablations import run_novelty_critical_ablations


def test_run_novelty_critical_ablations(production_configuration: LoadedConfiguration) -> None:
    report = run_novelty_critical_ablations(production_configuration.values)
    assert report.evaluated_configurations > 0
    assert report.scientific_outcome is ScientificOutcome.PASS
