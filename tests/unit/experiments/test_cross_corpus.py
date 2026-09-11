from __future__ import annotations

from fedact.domain.types import ScientificOutcome
from fedact.experiments.generalization import run_cross_corpus_generalization
from fedact.workflow import Application


def test_run_cross_corpus_generalization(application: Application) -> None:
    report = run_cross_corpus_generalization(application)
    assert report.lamda_cutoffs_fitted >= 0
    assert report.ember2024_cutoffs_fitted >= 0
    assert report.paired_action_cutoffs >= 0
    assert report.scientific_outcome in (
        ScientificOutcome.PASS,
        ScientificOutcome.INSUFFICIENT_EVIDENCE,
    )
