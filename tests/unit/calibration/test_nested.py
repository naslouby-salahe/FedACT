from __future__ import annotations

from fedact.calibration.nested import generate_calibration_candidates
from fedact.config.loading import LoadedConfiguration


def test_generate_calibration_candidates(production_configuration: LoadedConfiguration) -> None:
    candidates = generate_calibration_candidates(production_configuration.values)
    assert len(candidates) > 0
