from __future__ import annotations

from fedact.domain.types import ScientificOutcome
from fedact.experiments.robustness import run_federation_geometry_evaluation
from fedact.workflow import Application


def test_federation_requires_natural_multi_client_evidence(
    application: Application,
) -> None:
    report = run_federation_geometry_evaluation(application)
    assert report.geometries_tested == 0
    assert report.scientific_outcome is ScientificOutcome.INSUFFICIENT_EVIDENCE
