from __future__ import annotations

from fedact.workflow import Application
from fedact.domain.types import ScientificOutcome
from fedact.experiments.validation import run_action_certificate_validation


def test_run_action_certificate_validation(application: Application) -> None:
    report = run_action_certificate_validation(application)
    assert report.total_actions > 0
    assert report.scientific_outcome is ScientificOutcome.PASS
