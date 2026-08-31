from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

PositiveInt = Annotated[int, Field(gt=0)]
NonNegativeInt = Annotated[int, Field(ge=0)]
NonNegativeFloat = Annotated[float, Field(ge=0.0)]
PositiveFloat = Annotated[float, Field(gt=0.0)]
Probability = Annotated[float, Field(ge=0.0, le=1.0)]
ScalarCoefficient = Annotated[float, Field(gt=0.0, le=1.0)]
PercentagePoints = Annotated[float, Field(ge=0.0)]
PercentileCandidate = Annotated[int, Field(ge=0, le=100)]
RelativePosixPath = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_\-./]*$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ConfirmatoryFormat(StrEnum):
    WIN32_PE = "win32_pe"
    WIN64_PE = "win64_pe"


class FederationGeometry(StrEnum):
    REDUNDANT = "redundant"
    COMPLEMENTARY = "complementary"


class PrivateTransitionSparsityMode(StrEnum):
    DENSE = "dense"
    TEN_PERCENT_SPARSE = "ten_percent_sparse"


class CorruptedClientAttack(StrEnum):
    BASIS_ROTATION = "basis_rotation"
    FALSE_RANK_REPORTING = "false_rank_reporting"
    BETA_UNDER_REPORTING = "beta_under_reporting"
    TRANSITION_POISONING = "transition_poisoning"
    FABRICATED_COMPLEMENTARITY = "fabricated_complementarity"


class SyntheticCorruptionAttack(StrEnum):
    ROTATION = "rotation"
    RANK_MISREPORT = "rank_misreport"
    BETA_UNDERREPORT = "beta_underreport"
    POISONING = "poisoning"
    FABRICATED_COMPLEMENTARITY = "fabricated_complementarity"


class LamdaLabelRules(StrictModel):
    benign_detection_count: NonNegativeInt
    malware_minimum_detection_count: PositiveInt
    discard_detection_counts: list[NonNegativeInt]


class LamdaPreprocessingRules(StrictModel):
    raw_variance_threshold_when_required: NonNegativeFloat


class LamdaDatasetConfig(StrictModel):
    labels: LamdaLabelRules
    preprocessing: LamdaPreprocessingRules


class Ember2024DatasetConfig(StrictModel):
    confirmatory_formats: list[ConfirmatoryFormat]


class DatasetsConfig(StrictModel):
    lamda: LamdaDatasetConfig
    ember2024: Ember2024DatasetConfig


class TemporalModelParameters(StrictModel):
    minimum_consecutive_pairs: PositiveInt
    maximum_scalar_coefficient: ScalarCoefficient


class ProcessNoiseParameters(StrictModel):
    quantile: Probability


class TemporalConfig(StrictModel):
    historical_training_window_months: PositiveInt
    transition_interval_months: PositiveInt
    cutoff_step_months: PositiveInt
    full_retraining_interval_months: PositiveInt
    forecast_horizons_months: list[PositiveInt]
    primary_confirmatory_horizon_months: PositiveInt
    early_horizon_months: PositiveInt
    temporal_model: TemporalModelParameters
    process_noise: ProcessNoiseParameters


class TrainingConfig(StrictModel):
    initial_learning_rate: PositiveFloat
    final_learning_rate: PositiveFloat
    batch_size: PositiveInt
    maximum_epochs: PositiveInt
    early_stopping_patience_epochs: PositiveInt
    validation_fraction: Probability


class UncertaintyParameters(StrictModel):
    bootstrap_resamples: PositiveInt


class NuisanceRankSelection(StrictModel):
    candidates: list[PositiveInt]
    maximum: PositiveInt
    bootstrap_resamples: PositiveInt
    minimum_bootstrap_stability_fraction: Probability


class EigengapRatioSelection(StrictModel):
    candidates: list[PositiveFloat]
    default_without_nested_calibration: PositiveFloat


class TargetCoverageSelection(StrictModel):
    candidates: list[Probability]
    primary: Probability


class ControlSpanViolationAllowance(StrictModel):
    primary_alpha: Probability
    sensitivity_alpha: list[Probability]


class PrivateContaminationAllowance(StrictModel):
    primary_alpha: Probability
    sensitivity_alpha: list[Probability]
    minimum_history_residuals: PositiveInt


class HistoricalPlausibilityRadiusSelection(StrictModel):
    center_norm_quantile: Probability
    minimum_reference_centers: PositiveInt
    sensitivity_multipliers: list[PositiveFloat]


class CovarianceRegularizationSelection(StrictModel):
    primary_c: NonNegativeFloat
    sensitivity_c: list[NonNegativeFloat]


class ControlReconstructionGateRules(StrictModel):
    held_out_residual_quantile: Probability
    minimum_pass_fraction: Probability


class TailDiagnosticRules(StrictModel):
    maximum_absolute_excess_kurtosis: PositiveFloat
    maximum_flagged_coordinate_fraction: Probability


class IdentificationConfig(StrictModel):
    minimum_support_per_class: PositiveInt
    minimum_control_transition_replicates: PositiveInt
    uncertainty: UncertaintyParameters
    nuisance_rank: NuisanceRankSelection
    eigengap_ratio: EigengapRatioSelection
    target_coverage: TargetCoverageSelection
    control_span_violation: ControlSpanViolationAllowance
    private_contamination: PrivateContaminationAllowance
    historical_plausibility_radius: HistoricalPlausibilityRadiusSelection
    covariance_regularization: CovarianceRegularizationSelection
    control_reconstruction_gate: ControlReconstructionGateRules
    tail_diagnostic: TailDiagnosticRules


class AlignmentThresholdSelection(StrictModel):
    percentile_candidates: list[PercentileCandidate]


class AmbiguityWidthSelection(StrictModel):
    percentile_candidates: list[PercentileCandidate]


class ForecastSetDiameterAbstentionRule(StrictModel):
    historical_realized_diameter_quantile: Probability


class LeaveOneClientOutStabilityRule(StrictModel):
    minimum_unchanged_fraction: Probability


class RandomMatchingPolicy(StrictModel):
    minimum_exact_or_source_fraction: Probability


class CertificationConfig(StrictModel):
    alignment_threshold: AlignmentThresholdSelection
    ambiguity_width: AmbiguityWidthSelection
    forecast_set_diameter_abstention: ForecastSetDiameterAbstentionRule
    leave_one_client_out_stability: LeaveOneClientOutStabilityRule
    random_matching: RandomMatchingPolicy


class OperatorValidationBudgets(StrictModel):
    execution_timeout_seconds: PositiveFloat
    android_monkey_events: PositiveInt
    minimum_behavior_jaccard: Probability


class OperatorsConfig(StrictModel):
    minimum_valid_coverage: Probability
    maximum_composed_atomic_actions: PositiveInt
    validation: OperatorValidationBudgets


class AblationsConfig(StrictModel):
    zero_control_span_violation_budget: NonNegativeInt
    zero_private_contamination_budget: NonNegativeInt


class HardeningWeightSelection(StrictModel):
    candidates: list[Probability]
    maximum_clean_fnr_degradation_percentage_points: PercentagePoints


class MaximumActionsPerSampleSelection(StrictModel):
    candidates: list[PositiveInt]
    primary: PositiveInt


class HardeningConfig(StrictModel):
    weight: HardeningWeightSelection
    maximum_actions_per_sample: MaximumActionsPerSampleSelection


class BaselinesConfig(StrictModel):
    point_ridge_relative: PositiveFloat


class CorruptedClientAllowanceParameters(StrictModel):
    basis_rotation_degrees: NonNegativeFloat
    false_rank_increment: PositiveInt
    beta_multiplier: ScalarCoefficient
    transition_poisoning_sigma: PositiveFloat
    fabricated_complementarity_rotation_degrees: NonNegativeFloat


class CorruptedClientAllowanceConfig(StrictModel):
    counts: list[NonNegativeInt]
    attacks: list[CorruptedClientAttack]
    parameters: CorruptedClientAllowanceParameters


class RealStressConfig(StrictModel):
    control_support_fractions: list[Probability]
    control_transition_noise_sigma_multipliers: list[PositiveFloat]


class RobustnessConfig(StrictModel):
    corrupted_client_allowance: CorruptedClientAllowanceConfig
    real_stress: RealStressConfig


class BootstrapStatisticsConfig(StrictModel):
    resamples: PositiveInt


class WilcoxonSettings(StrictModel):
    maximum_nonzero_pairs_for_exact: PositiveInt


class MultiplicityControl(StrictModel):
    q: Probability


class MaterialEffectThresholds(StrictModel):
    early_horizon_fnr_absolute_reduction_percentage_points: PercentagePoints
    action_certification_precision_absolute_increase: Probability
    maximum_coverage_deficit_absolute: Probability


class StatisticsConfig(StrictModel):
    confidence_level: Probability
    minimum_paired_cutoffs: PositiveInt
    maximum_missing_cutoff_fraction: Probability
    bootstrap: BootstrapStatisticsConfig
    wilcoxon: WilcoxonSettings
    multiplicity: MultiplicityControl
    minimum_material_effects: MaterialEffectThresholds


class SeedsConfig(StrictModel):
    representation: list[NonNegativeInt]
    detector_training: list[NonNegativeInt]
    synthetic_generation: list[NonNegativeInt]
    synthetic_noise: list[NonNegativeInt]
    operator: list[NonNegativeInt]
    calibration: list[NonNegativeInt]
    baseline: list[NonNegativeInt]
    analysis: list[NonNegativeInt]
    client_selection: list[NonNegativeInt]


class SyntheticDefaults(StrictModel):
    nuisance_dimension_fraction: Probability
    control_malicious_amplitude_ratio: PositiveFloat
    pairwise_principal_angle_degrees: NonNegativeFloat
    common_intersection_dimension: NonNegativeInt
    federation_client_count: PositiveInt
    federation_geometry: FederationGeometry
    control_sample_size: PositiveInt
    malicious_sample_size: PositiveInt
    control_span_violation_over_sigma: NonNegativeFloat
    synchronized_nuisance_over_sigma: NonNegativeFloat
    private_transition_norm_over_sigma: NonNegativeFloat
    private_transition_sparsity_mode: PrivateTransitionSparsityMode
    outlier_client_count: NonNegativeInt
    spectral_conditioning_ratio: Probability
    action_rotation_angle_degrees: NonNegativeFloat


class NuisanceDimensionSweep(StrictModel):
    fractions: list[Probability]


class FederationSweep(StrictModel):
    client_counts: list[PositiveInt]
    geometries: list[FederationGeometry]
    matched_total_samples: bool


class PrivateTransitionSweep(StrictModel):
    norm_over_sigma: list[NonNegativeFloat]
    sparsity_modes: list[PrivateTransitionSparsityMode]
    sparse_fraction: Probability


class OutlierClientStressSweep(StrictModel):
    corrupted_client_counts: list[NonNegativeInt]
    attacks: list[SyntheticCorruptionAttack]


class SyntheticSweeps(StrictModel):
    nuisance_dimension: NuisanceDimensionSweep
    control_malicious_amplitude_ratio: list[PositiveFloat]
    pairwise_principal_angle_degrees: list[NonNegativeFloat]
    common_intersection_dimension: list[NonNegativeInt]
    federation: FederationSweep
    control_sample_size: list[PositiveInt]
    malicious_sample_size: list[PositiveInt]
    control_span_violation_over_sigma: list[NonNegativeFloat]
    synchronized_nuisance_over_sigma: list[NonNegativeFloat]
    private_transition: PrivateTransitionSweep
    outlier_client_stress: OutlierClientStressSweep
    spectral_conditioning_ratio: list[Probability]
    action_rotation_angle_degrees: list[NonNegativeFloat]


class SyntheticConfig(StrictModel):
    base_sigma: PositiveFloat
    shared_transition_norm_over_sigma: PositiveFloat
    independent_draws_per_grid_cell: PositiveInt
    nested_noise_draws_per_seed: PositiveInt
    defaults: SyntheticDefaults
    sweeps: SyntheticSweeps


class ClientSelectionConfig(StrictModel):
    budget_fractions: list[Probability]
    d_optimal_ridge: PositiveFloat


class SolverTolerances(StrictModel):
    relative_tolerance: PositiveFloat
    absolute_tolerance: PositiveFloat
    duality_gap_tolerance: PositiveFloat
    maximum_iterations: PositiveInt


class NumericalContract(StrictModel):
    scale_standardization_floor: PositiveFloat
    rank_clip_epsilon_relative: PositiveFloat
    zero_displacement_floor: PositiveFloat
    projection_tie_tolerance: PositiveFloat
    condition_number_limit: PositiveFloat
    solver: SolverTolerances


class SignificantFiguresPolicy(StrictModel):
    percentages_and_rates: PositiveInt
    raw_action_width_and_alignment: PositiveInt
    effect_sizes_and_p_values: PositiveInt


class ReportingConfig(StrictModel):
    significant_figures: SignificantFiguresPolicy
    p_value_display_threshold: PositiveFloat


class WorkspaceDirectories(StrictModel):
    preprocessing: RelativePosixPath
    shared_artifacts: RelativePosixPath
    shared_models: RelativePosixPath
    shared_scores: RelativePosixPath
    shared_fitted: RelativePosixPath
    shared_baselines: RelativePosixPath
    shared_derived: RelativePosixPath
    shared_provenance: RelativePosixPath
    experiments: RelativePosixPath
    cache: RelativePosixPath
    staging: RelativePosixPath
    result_experiments: RelativePosixPath
    project_summary: RelativePosixPath
    reproducibility: RelativePosixPath


class WorkspaceConfig(StrictModel):
    configuration_file: RelativePosixPath
    outputs_root: RelativePosixPath
    results_root: RelativePosixPath
    directories: WorkspaceDirectories
    experiment_directories: list[str]


class FedActConfig(StrictModel):
    datasets: DatasetsConfig
    temporal: TemporalConfig
    training: TrainingConfig
    identification: IdentificationConfig
    certification: CertificationConfig
    operators: OperatorsConfig
    ablations: AblationsConfig
    hardening: HardeningConfig
    baselines: BaselinesConfig
    robustness: RobustnessConfig
    statistics: StatisticsConfig
    seeds: SeedsConfig
    synthetic: SyntheticConfig
    client_selection: ClientSelectionConfig
    numerical: NumericalContract
    reporting: ReportingConfig
    workspace: WorkspaceConfig
