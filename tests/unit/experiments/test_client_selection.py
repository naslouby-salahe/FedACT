from __future__ import annotations

from fedact.workflow import Application
from fedact.domain.types import ScientificOutcome
from fedact.experiments.robustness import run_communication_limited_client_selection


def test_run_communication_limited_client_selection(
    application: Application,
) -> None:
    report = run_communication_limited_client_selection(application)
    assert report.budget_fractions_tested > 0
    assert report.scientific_outcome is ScientificOutcome.PASS
