from __future__ import annotations

from fedact.domain.types import ScientificOutcome
from fedact.experiments.robustness import run_communication_limited_client_selection
from fedact.workflow import Application


def test_client_selection_requires_materialized_client_information(
    application: Application,
) -> None:
    report = run_communication_limited_client_selection(application)
    assert report.budget_fractions_tested == 0
    assert report.scientific_outcome is ScientificOutcome.INSUFFICIENT_EVIDENCE
