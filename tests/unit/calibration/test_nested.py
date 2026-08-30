from __future__ import annotations

from fedact.calibration.nested import (
    HardeningWeightDegradation,
    HardeningWeightDegradations,
    generate_calibration_candidates,
)
from fedact.config.loading import LoadedConfiguration


def test_generate_calibration_candidates(production_configuration: LoadedConfiguration) -> None:
    config = production_configuration.values
    clean_degradations = HardeningWeightDegradations(
        entries=tuple(
            HardeningWeightDegradation(hardening_weight=weight, clean_degradation=0.5)
            for weight in config.hardening.weight.candidates
        )
    )
    candidates = generate_calibration_candidates(config, clean_degradations)
    assert len(candidates) > 0
