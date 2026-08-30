from __future__ import annotations

from fedact.config.loading import LoadedConfiguration
from fedact.domain.enums import ScientificOutcome
from fedact.experiments.cross_corpus import run_cross_corpus_generalization


def test_run_cross_corpus_generalization(production_configuration: LoadedConfiguration) -> None:
    report = run_cross_corpus_generalization(production_configuration.values)
    assert 0.0 <= report.mean_transfer_fnr <= 1.0
    assert report.scientific_outcome in (
        ScientificOutcome.PASS,
        ScientificOutcome.INSUFFICIENT_EVIDENCE,
    )
