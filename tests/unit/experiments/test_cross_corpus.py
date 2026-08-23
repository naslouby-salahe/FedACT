from __future__ import annotations

from fedact.config.loading import LoadedConfiguration
from fedact.domain.enums import ScientificOutcome
from fedact.experiments.cross_corpus import run_cross_corpus_generalization


def test_run_cross_corpus_generalization(production_configuration: LoadedConfiguration) -> None:
    report = run_cross_corpus_generalization(production_configuration.values)
    assert report.generalization_valid
    assert report.scientific_outcome is ScientificOutcome.PASS
