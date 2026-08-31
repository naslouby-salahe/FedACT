from __future__ import annotations

from fedact.app import Application
from fedact.domain.enums import ScientificOutcome
from fedact.experiments.prospective_evaluation import run_prospective_fedact_evaluation


def test_run_prospective_fedact_evaluation(application: Application) -> None:
    report = run_prospective_fedact_evaluation(application)
    assert report.total_evaluations > 0
    assert 0.0 <= report.mean_false_negative_rate <= 1.0
    assert 0.0 <= report.mean_certification_rate <= 1.0
    assert report.scientific_outcome in (
        ScientificOutcome.PASS,
        ScientificOutcome.INSUFFICIENT_EVIDENCE,
    )
