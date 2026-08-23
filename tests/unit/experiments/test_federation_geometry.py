from __future__ import annotations

from fedact.config.loading import LoadedConfiguration
from fedact.domain.enums import ScientificOutcome
from fedact.experiments.federation_geometry import run_federation_and_complementarity_evaluation


def test_run_federation_and_complementarity_evaluation(
    production_configuration: LoadedConfiguration,
) -> None:
    report = run_federation_and_complementarity_evaluation(production_configuration.values)
    assert report.geometries_tested > 0
    assert report.scientific_outcome is ScientificOutcome.PASS
