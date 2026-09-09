from __future__ import annotations

from fedact.domain.types import ScientificOutcome
from fedact.experiments.robustness import run_federation_geometry_evaluation
from fedact.workflow import Application


def test_run_federation_and_complementarity_evaluation(
    application: Application,
) -> None:
    report = run_federation_geometry_evaluation(application)
    assert report.geometries_tested > 0
    assert report.scientific_outcome is ScientificOutcome.PASS
