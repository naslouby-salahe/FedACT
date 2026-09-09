from __future__ import annotations

from fedact.domain.types import ScientificOutcome
from fedact.experiments.generalization import run_prospective_fedact_evaluation
from fedact.workflow import Application


def test_prospective_evaluation_never_fabricates_missing_lamda_evidence(
    application: Application,
) -> None:
    report = run_prospective_fedact_evaluation(application)
    assert report.total_evaluations == 0
    assert 0.0 <= report.mean_false_negative_rate <= 1.0
    assert 0.0 <= report.mean_certification_rate <= 1.0
    assert report.scientific_outcome is ScientificOutcome.INSUFFICIENT_EVIDENCE
