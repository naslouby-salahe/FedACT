from __future__ import annotations

from fedact.app import Application
from fedact.domain.enums import ScientificOutcome
from fedact.experiments.synthetic_geometry import run_synthetic_geometry_sweeps


def test_synthetic_geometry_sweeps_executes_and_passes(
    application: Application,
) -> None:
    report = run_synthetic_geometry_sweeps(application)
    assert report.total_cells > 0
    assert report.passed_cells == report.total_cells
    assert report.mechanism_valid
    assert report.scientific_outcome is ScientificOutcome.PASS
