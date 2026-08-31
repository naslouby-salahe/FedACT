from __future__ import annotations

from fedact.config.loading import LoadedConfiguration
from fedact.domain.enums import ScientificOutcome
from fedact.experiments.statistical_synthesis import run_statistical_synthesis


def test_run_statistical_synthesis(production_configuration: LoadedConfiguration) -> None:
    config = production_configuration.values
    report = run_statistical_synthesis(
        prospective_fnr=0.08,
        clean_fnr_degradation=1.0,
        coverage=0.99,
        maximum_coverage_deficit=(
            config.statistics.minimum_material_effects.maximum_coverage_deficit_absolute
        ),
        maximum_clean_fnr_degradation=(
            config.hardening.weight.maximum_clean_fnr_degradation_percentage_points
        ),
        control_span_alphas=tuple(config.identification.control_span_violation.sensitivity_alpha),
        private_contamination_alphas=tuple(
            config.identification.private_contamination.sensitivity_alpha
        ),
        radius_multipliers=tuple(
            config.identification.historical_plausibility_radius.sensitivity_multipliers
        ),
        alignment_percentiles=tuple(config.certification.alignment_threshold.percentile_candidates),
        ambiguity_percentiles=tuple(config.certification.ambiguity_width.percentile_candidates),
        forecast_horizons=tuple(config.temporal.forecast_horizons_months),
        nuisance_ranks=tuple(config.identification.nuisance_rank.candidates),
        coverage_levels=tuple(config.identification.target_coverage.candidates),
    )
    assert report.coverage_satisfied
    assert report.clean_cost_satisfied
    assert report.overall_scientific_outcome is ScientificOutcome.PASS
    assert report.sensitivity_coordinates
