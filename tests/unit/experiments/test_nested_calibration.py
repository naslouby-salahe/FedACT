from __future__ import annotations

from fedact.calibration.nested import run_nested_calibration
from fedact.config.loading import LoadedConfiguration


def test_run_nested_calibration_produces_candidates_for_every_grid_cell(
    production_configuration: LoadedConfiguration,
) -> None:
    config = production_configuration.values
    candidates = run_nested_calibration(config)
    align_count = len(config.certification.alignment_threshold.percentile_candidates)
    ambiguity_count = len(config.certification.ambiguity_width.percentile_candidates)
    weight_count = len(config.hardening.weight.candidates)
    assert len(candidates) == align_count * ambiguity_count * weight_count
    assert all(0.0 <= candidate.observed_certification_rate <= 1.0 for candidate in candidates)
