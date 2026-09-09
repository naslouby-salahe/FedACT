from __future__ import annotations

from fedact.workflow import Application
from fedact.domain.types import ScientificOutcome
from fedact.experiments.robustness import run_novelty_critical_ablations


def test_run_novelty_critical_ablations(application: Application) -> None:
    report = run_novelty_critical_ablations(application)
    assert report.evaluated_configurations > 0
    assert report.scientific_outcome is ScientificOutcome.PASS
