from __future__ import annotations

from fedact.config.loading import LoadedConfiguration
from fedact.domain.enums import ScientificOutcome
from fedact.experiments.prospective import run_prospective_fedact_evaluation


def test_run_prospective_fedact_evaluation(production_configuration: LoadedConfiguration) -> None:
    report = run_prospective_fedact_evaluation(production_configuration.values)
    assert report.total_evaluations > 0
    assert report.scientific_outcome is ScientificOutcome.PASS
