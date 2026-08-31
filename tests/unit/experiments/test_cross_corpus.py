from __future__ import annotations

from fedact.app import Application
from fedact.domain.enums import ScientificOutcome
from fedact.experiments.cross_corpus import run_cross_corpus_generalization


def test_run_cross_corpus_generalization(application: Application) -> None:
    report = run_cross_corpus_generalization(application)
    assert 0.0 <= report.mean_transfer_fnr <= 1.0
    assert report.scientific_outcome in (
        ScientificOutcome.PASS,
        ScientificOutcome.INSUFFICIENT_EVIDENCE,
    )
