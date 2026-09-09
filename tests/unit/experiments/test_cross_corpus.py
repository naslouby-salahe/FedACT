from __future__ import annotations

from fedact.workflow import Application
from fedact.domain.types import ScientificOutcome
from fedact.experiments.generalization import run_cross_corpus_generalization


def test_run_cross_corpus_generalization(application: Application) -> None:
    report = run_cross_corpus_generalization(application)
    assert 0.0 <= report.mean_transfer_fnr <= 1.0
    assert report.scientific_outcome in (
        ScientificOutcome.PASS,
        ScientificOutcome.INSUFFICIENT_EVIDENCE,
    )
