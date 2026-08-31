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
    candidates = generate_calibration_candidates(
        alignment_percentile_candidates=tuple(
            config.certification.alignment_threshold.percentile_candidates
        ),
        ambiguity_width_percentile_candidates=tuple(
            config.certification.ambiguity_width.percentile_candidates
        ),
        hardening_weight_candidates=tuple(config.hardening.weight.candidates),
        maximum_nuisance_rank=config.identification.nuisance_rank.maximum,
        eigengap_regularization=config.numerical.rank_clip_epsilon_relative,
        scale_standardization_floor=config.numerical.scale_standardization_floor,
        historical_realized_diameter_quantile=(
            config.certification.forecast_set_diameter_abstention.historical_realized_diameter_quantile
        ),
        clean_degradations=clean_degradations,
    )
    assert len(candidates) > 0
