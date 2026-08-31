from __future__ import annotations

from fedact.app import Application
from fedact.domain.enums import ScientificOutcome
from fedact.experiments.federation import run_federation_geometry_evaluation


def test_run_federation_and_complementarity_evaluation(
    application: Application,
) -> None:
    report = run_federation_geometry_evaluation(application)
    assert report.geometries_tested > 0
    assert report.scientific_outcome is ScientificOutcome.PASS
