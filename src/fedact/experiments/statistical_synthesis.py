from __future__ import annotations

from dataclasses import dataclass

from fedact.analysis.comparisons import (
    CutoffAggregate,
    PairedContrastInputs,
    build_paired_contrast,
    contrast_effect_direction,
)
from fedact.analysis.sensitivity import (
    SensitivityAxis,
    SensitivityCoordinate,
    enumerate_sensitivity_coordinates,
)
from fedact.analysis.statistics import (
    BenjaminiHochbergOutcome,
    BootstrapEstimate,
    WilcoxonSignedRankResult,
    benjamini_hochberg_correction,
    cutoff_clustered_bca_bootstrap,
    matched_pairs_rank_biserial_effect_size,
    paired_wilcoxon_signed_rank_test,
)
from fedact.domain.enums import ScientificOutcome
from fedact.domain.records import (
    CutoffCount,
    DegradationValue,
    MetricRate,
    ResampleCount,
    SeedValue,
    ThresholdValue,
    ValidationFlag,
)


@dataclass(frozen=True)
class ConfirmatoryContrastOutcome:
    contrast_inputs: PairedContrastInputs
    bootstrap: BootstrapEstimate | None
    wilcoxon: WilcoxonSignedRankResult | None
    multiplicity: BenjaminiHochbergOutcome


@dataclass(frozen=True)
class StatisticalSynthesisReport:
    coverage_satisfied: ValidationFlag
    clean_cost_satisfied: ValidationFlag
    overall_scientific_outcome: ScientificOutcome
    sensitivity_coordinates: tuple[SensitivityCoordinate, ...]
    contrast_outcome: ConfirmatoryContrastOutcome | None


def _evaluate_primary_contrast(
    method_a: tuple[CutoffAggregate, ...],
    method_b: tuple[CutoffAggregate, ...],
    minimum_paired_cutoffs: CutoffCount,
    maximum_missing_cutoff_fraction: MetricRate,
    bootstrap_resamples: ResampleCount,
    confidence_level: MetricRate,
    maximum_nonzero_pairs_for_exact: CutoffCount,
    multiplicity_q: MetricRate,
    seed: SeedValue,
) -> ConfirmatoryContrastOutcome:
    contrast = build_paired_contrast(
        method_a=method_a,
        method_b=method_b,
        minimum_paired_cutoffs=minimum_paired_cutoffs,
        maximum_missing_cutoff_fraction=maximum_missing_cutoff_fraction,
    )
    if not contrast.sufficient:
        return ConfirmatoryContrastOutcome(
            contrast_inputs=contrast,
            bootstrap=None,
            wilcoxon=None,
            multiplicity=benjamini_hochberg_correction((), multiplicity_q),
        )
    bootstrap = cutoff_clustered_bca_bootstrap(
        contrast.paired_differences,
        resamples=bootstrap_resamples,
        confidence_level=confidence_level,
        seed=seed,
    )
    wilcoxon = paired_wilcoxon_signed_rank_test(
        contrast.paired_differences,
        maximum_nonzero_pairs_for_exact=maximum_nonzero_pairs_for_exact,
    )
    contrast_effect_direction(contrast.paired_differences)
    matched_pairs_rank_biserial_effect_size(contrast.paired_differences)
    multiplicity = benjamini_hochberg_correction((wilcoxon.p_value,), multiplicity_q)
    return ConfirmatoryContrastOutcome(
        contrast_inputs=contrast,
        bootstrap=bootstrap,
        wilcoxon=wilcoxon,
        multiplicity=multiplicity,
    )


def run_statistical_synthesis(
    prospective_fnr: MetricRate,
    clean_fnr_degradation: DegradationValue,
    coverage: MetricRate,
    maximum_coverage_deficit: MetricRate,
    maximum_clean_fnr_degradation: DegradationValue,
    control_span_alphas: tuple[ThresholdValue, ...],
    private_contamination_alphas: tuple[ThresholdValue, ...],
    radius_multipliers: tuple[ThresholdValue, ...],
    alignment_percentiles: tuple[ThresholdValue, ...],
    ambiguity_percentiles: tuple[ThresholdValue, ...],
    forecast_horizons: tuple[ThresholdValue, ...],
    nuisance_ranks: tuple[ThresholdValue, ...],
    coverage_levels: tuple[ThresholdValue, ...],
    minimum_paired_cutoffs: CutoffCount,
    maximum_missing_cutoff_fraction: MetricRate,
    bootstrap_resamples: ResampleCount,
    confidence_level: MetricRate,
    maximum_nonzero_pairs_for_exact: CutoffCount,
    multiplicity_q: MetricRate,
    statistics_seed: SeedValue,
    certified_series: tuple[CutoffAggregate, ...] = (),
    ambiguous_series: tuple[CutoffAggregate, ...] = (),
) -> StatisticalSynthesisReport:
    coverage_satisfied = coverage >= (1.0 - maximum_coverage_deficit)
    clean_cost_satisfied = clean_fnr_degradation <= maximum_clean_fnr_degradation
    outcome = (
        ScientificOutcome.PASS
        if coverage_satisfied and clean_cost_satisfied
        else ScientificOutcome.FAIL
    )
    coordinates = enumerate_sensitivity_coordinates(
        control_span_alphas=control_span_alphas,
        private_contamination_alphas=private_contamination_alphas,
        radius_multipliers=radius_multipliers,
        alignment_percentiles=alignment_percentiles,
        ambiguity_percentiles=ambiguity_percentiles,
        forecast_horizons=forecast_horizons,
        nuisance_ranks=nuisance_ranks,
        coverage_levels=coverage_levels,
    )
    if not any(coordinate.axis is SensitivityAxis.TARGET_COVERAGE for coordinate in coordinates):
        outcome = ScientificOutcome.INSUFFICIENT_EVIDENCE

    contrast_outcome = None
    if certified_series and ambiguous_series:
        contrast_outcome = _evaluate_primary_contrast(
            method_a=certified_series,
            method_b=ambiguous_series,
            minimum_paired_cutoffs=minimum_paired_cutoffs,
            maximum_missing_cutoff_fraction=maximum_missing_cutoff_fraction,
            bootstrap_resamples=bootstrap_resamples,
            confidence_level=confidence_level,
            maximum_nonzero_pairs_for_exact=maximum_nonzero_pairs_for_exact,
            multiplicity_q=multiplicity_q,
            seed=statistics_seed,
        )
    return StatisticalSynthesisReport(
        coverage_satisfied=coverage_satisfied,
        clean_cost_satisfied=clean_cost_satisfied,
        overall_scientific_outcome=outcome,
        sensitivity_coordinates=coordinates,
        contrast_outcome=contrast_outcome,
    )
