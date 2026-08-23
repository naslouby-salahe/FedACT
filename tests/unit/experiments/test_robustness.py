from __future__ import annotations

from fedact.config.loading import LoadedConfiguration
from fedact.domain.enums import ScientificOutcome
from fedact.experiments.robustness import run_robustness_and_failure_boundary_evaluation


def test_run_robustness_and_failure_boundary_evaluation(
    production_configuration: LoadedConfiguration,
) -> None:
    report = run_robustness_and_failure_boundary_evaluation(production_configuration.values)
    assert report.boundary_points_tested > 0
    assert report.scientific_outcome is ScientificOutcome.PASS
