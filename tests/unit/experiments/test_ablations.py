from __future__ import annotations

from fedact.domain.types import ScientificOutcome
from fedact.experiments.robustness import run_novelty_critical_ablations
from fedact.workflow import Application


def test_ablation_requires_completed_prospective_evidence(application: Application) -> None:
    report = run_novelty_critical_ablations(application)
    assert report.evaluated_configurations == 0
    assert report.scientific_outcome is ScientificOutcome.INSUFFICIENT_EVIDENCE
