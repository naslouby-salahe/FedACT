from __future__ import annotations

from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict

from fedact.domain.types import (
    AngleDegrees,
    BatchSize,
    BudgetAmount,
    ClientCount,
    ConditionNumberLimit,
    ConfidenceLevel,
    ConfirmatoryFormat,
    CorruptedClientAttack,
    CutoffCount,
    DetectionCount,
    DrawCount,
    EigengapRatio,
    EpochCount,
    Epsilon,
    EventCount,
    ExperimentDirectoryName,
    FederationClientCount,
    FederationGeometry,
    Fraction,
    IntersectionDimension,
    KurtosisExcess,
    LearningRate,
    MatchedTotalSamplesFlag,
    MaximumIterations,
    MinimumDetectionCount,
    PercentagePoints,
    PercentileValue,
    PrivateTransitionSparsityMode,
    Probability,
    RankDimension,
    RankIncrement,
    ReferenceCenterCount,
    RelativePosixPath,
    ReplicateCount,
    ResampleCount,
    SampleSize,
    ScalarCoefficient,
    SeedValue,
    SensitivityMultiplier,
    Sigma,
    SimilarityScore,
    StandardizationFloor,
    SupportThreshold,
    SyntheticCorruptionAttack,
    TimeoutSeconds,
    Tolerance,
    ToolchainIdentifier,
    VarianceThreshold,
    WindowSpanMonths,
    ZeroDisplacementFloor,
)


class StrictModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class LamdaLabelRules(StrictModel):
    benign_detection_count: DetectionCount
    malware_minimum_detection_count: MinimumDetectionCount
    discard_detection_counts: list[DetectionCount]


class LamdaPreprocessingRules(StrictModel):
    raw_variance_threshold_when_required: VarianceThreshold


class LamdaDatasetConfig(StrictModel):
    labels: LamdaLabelRules
    preprocessing: LamdaPreprocessingRules


class Ember2024DatasetConfig(StrictModel):
    confirmatory_formats: list[ConfirmatoryFormat]


class DatasetsConfig(StrictModel):
    lamda: LamdaDatasetConfig
    ember2024: Ember2024DatasetConfig


class TemporalModelParameters(StrictModel):
    minimum_consecutive_pairs: ReplicateCount
    maximum_scalar_coefficient: ScalarCoefficient


class ProcessNoiseParameters(StrictModel):
    quantile: Probability


class TemporalConfig(StrictModel):
    historical_training_window_months: WindowSpanMonths
    transition_interval_months: WindowSpanMonths
    cutoff_step_months: WindowSpanMonths
    full_retraining_interval_months: WindowSpanMonths
    forecast_horizons_months: list[WindowSpanMonths]
    primary_confirmatory_horizon_months: WindowSpanMonths
    early_horizon_months: WindowSpanMonths
    temporal_model: TemporalModelParameters
    process_noise: ProcessNoiseParameters


class TrainingConfig(StrictModel):
    initial_learning_rate: LearningRate
    final_learning_rate: LearningRate
    batch_size: BatchSize
    maximum_epochs: EpochCount
    early_stopping_patience_epochs: EpochCount
    validation_fraction: Fraction


class UncertaintyParameters(StrictModel):
    bootstrap_resamples: ResampleCount


class NuisanceRankSelection(StrictModel):
    candidates: list[RankDimension]
    maximum: RankDimension
    bootstrap_resamples: ResampleCount
    minimum_bootstrap_stability_fraction: Fraction


class EigengapRatioSelection(StrictModel):
    candidates: list[EigengapRatio]
    default_without_nested_calibration: EigengapRatio


class TargetCoverageSelection(StrictModel):
    candidates: list[Probability]
    primary: Probability


class ControlSpanViolationAllowance(StrictModel):
    primary_alpha: Probability
    sensitivity_alpha: list[Probability]


class PrivateContaminationAllowance(StrictModel):
    primary_alpha: Probability
    sensitivity_alpha: list[Probability]
    minimum_history_residuals: ReplicateCount


class HistoricalPlausibilityRadiusSelection(StrictModel):
    center_norm_quantile: Probability
    minimum_reference_centers: ReferenceCenterCount
    sensitivity_multipliers: list[SensitivityMultiplier]


class CovarianceRegularizationSelection(StrictModel):
    primary_c: BudgetAmount
    sensitivity_c: list[BudgetAmount]


class ControlReconstructionGateRules(StrictModel):
    held_out_residual_quantile: Probability
    minimum_pass_fraction: Fraction


class TailDiagnosticRules(StrictModel):
    maximum_absolute_excess_kurtosis: KurtosisExcess
    maximum_flagged_coordinate_fraction: Fraction


class IdentificationConfig(StrictModel):
    minimum_support_per_class: SupportThreshold
    minimum_control_transition_replicates: ReplicateCount
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
    percentile_candidates: list[PercentileValue]


class AmbiguityWidthSelection(StrictModel):
    percentile_candidates: list[PercentileValue]


class ForecastSetDiameterAbstentionRule(StrictModel):
    historical_realized_diameter_quantile: Probability


class LeaveOneClientOutStabilityRule(StrictModel):
    minimum_unchanged_fraction: Fraction


class RandomMatchingPolicy(StrictModel):
    minimum_exact_or_source_fraction: Fraction


class CertificationConfig(StrictModel):
    alignment_threshold: AlignmentThresholdSelection
    ambiguity_width: AmbiguityWidthSelection
    forecast_set_diameter_abstention: ForecastSetDiameterAbstentionRule
    leave_one_client_out_stability: LeaveOneClientOutStabilityRule
    random_matching: RandomMatchingPolicy


class OperatorValidationBudgets(StrictModel):
    execution_timeout_seconds: TimeoutSeconds
    android_monkey_events: EventCount
    minimum_behavior_jaccard: SimilarityScore
    android_system_image: ToolchainIdentifier


class OperatorsConfig(StrictModel):
    minimum_valid_coverage: Fraction
    maximum_composed_atomic_actions: ReplicateCount
    validation: OperatorValidationBudgets


class AblationsConfig(StrictModel):
    zero_control_span_violation_budget: BudgetAmount
    zero_private_contamination_budget: BudgetAmount


class HardeningWeightSelection(StrictModel):
    candidates: list[Probability]
    maximum_clean_fnr_degradation_percentage_points: PercentagePoints


class MaximumActionsPerSampleSelection(StrictModel):
    candidates: list[ReplicateCount]
    primary: ReplicateCount


class HardeningConfig(StrictModel):
    weight: HardeningWeightSelection
    maximum_actions_per_sample: MaximumActionsPerSampleSelection


class BaselinesConfig(StrictModel):
    point_ridge_relative: Epsilon


class CorruptedClientAllowanceParameters(StrictModel):
    basis_rotation_degrees: AngleDegrees
    false_rank_increment: RankIncrement
    beta_multiplier: ScalarCoefficient
    transition_poisoning_sigma: Sigma
    fabricated_complementarity_rotation_degrees: AngleDegrees


class CorruptedClientAllowanceConfig(StrictModel):
    counts: list[ClientCount]
    attacks: list[CorruptedClientAttack]
    parameters: CorruptedClientAllowanceParameters


class RealStressConfig(StrictModel):
    control_support_fractions: list[Fraction]
    control_transition_noise_sigma_multipliers: list[SensitivityMultiplier]


class RobustnessConfig(StrictModel):
    corrupted_client_allowance: CorruptedClientAllowanceConfig
    real_stress: RealStressConfig


class BootstrapStatisticsConfig(StrictModel):
    resamples: ResampleCount


class WilcoxonSettings(StrictModel):
    maximum_nonzero_pairs_for_exact: CutoffCount


class MultiplicityControl(StrictModel):
    q: Probability


class MaterialEffectThresholds(StrictModel):
    early_horizon_fnr_absolute_reduction_percentage_points: PercentagePoints
    action_certification_precision_absolute_increase: Probability
    maximum_coverage_deficit_absolute: Probability


class StatisticsConfig(StrictModel):
    confidence_level: ConfidenceLevel
    minimum_paired_cutoffs: CutoffCount
    maximum_missing_cutoff_fraction: Fraction
    bootstrap: BootstrapStatisticsConfig
    wilcoxon: WilcoxonSettings
    multiplicity: MultiplicityControl
    minimum_material_effects: MaterialEffectThresholds


class SeedsConfig(StrictModel):
    representation: list[SeedValue]
    detector_training: list[SeedValue]
    synthetic_generation: list[SeedValue]
    synthetic_noise: list[SeedValue]
    operator: list[SeedValue]
    calibration: list[SeedValue]
    baseline: list[SeedValue]
    analysis: list[SeedValue]
    client_selection: list[SeedValue]


class SyntheticDefaults(StrictModel):
    nuisance_dimension_fraction: Fraction
    control_malicious_amplitude_ratio: SensitivityMultiplier
    pairwise_principal_angle_degrees: AngleDegrees
    common_intersection_dimension: IntersectionDimension
    federation_client_count: FederationClientCount
    federation_geometry: FederationGeometry
    control_sample_size: SampleSize
    malicious_sample_size: SampleSize
    control_span_violation_over_sigma: BudgetAmount
    synchronized_nuisance_over_sigma: BudgetAmount
    private_transition_norm_over_sigma: BudgetAmount
    private_transition_sparsity_mode: PrivateTransitionSparsityMode
    outlier_client_count: ClientCount
    spectral_conditioning_ratio: Probability
    action_rotation_angle_degrees: AngleDegrees


class NuisanceDimensionSweep(StrictModel):
    fractions: list[Fraction]


class FederationSweep(StrictModel):
    client_counts: list[FederationClientCount]
    geometries: list[FederationGeometry]
    matched_total_samples: MatchedTotalSamplesFlag


class PrivateTransitionSweep(StrictModel):
    norm_over_sigma: list[BudgetAmount]
    sparsity_modes: list[PrivateTransitionSparsityMode]
    sparse_fraction: Fraction


class OutlierClientStressSweep(StrictModel):
    corrupted_client_counts: list[ClientCount]
    attacks: list[SyntheticCorruptionAttack]


class SyntheticSweeps(StrictModel):
    nuisance_dimension: NuisanceDimensionSweep
    control_malicious_amplitude_ratio: list[SensitivityMultiplier]
    pairwise_principal_angle_degrees: list[AngleDegrees]
    common_intersection_dimension: list[IntersectionDimension]
    federation: FederationSweep
    control_sample_size: list[SampleSize]
    malicious_sample_size: list[SampleSize]
    control_span_violation_over_sigma: list[BudgetAmount]
    synchronized_nuisance_over_sigma: list[BudgetAmount]
    private_transition: PrivateTransitionSweep
    outlier_client_stress: OutlierClientStressSweep
    spectral_conditioning_ratio: list[Probability]
    action_rotation_angle_degrees: list[AngleDegrees]


class SyntheticConfig(StrictModel):
    base_sigma: Sigma
    shared_transition_norm_over_sigma: Sigma
    independent_draws_per_grid_cell: DrawCount
    nested_noise_draws_per_seed: DrawCount
    defaults: SyntheticDefaults
    sweeps: SyntheticSweeps


class ClientSelectionConfig(StrictModel):
    budget_fractions: list[Fraction]
    d_optimal_ridge: Epsilon


class SolverTolerances(StrictModel):
    relative_tolerance: Tolerance
    absolute_tolerance: Tolerance
    duality_gap_tolerance: Tolerance
    maximum_iterations: MaximumIterations


class NumericalContract(StrictModel):
    scale_standardization_floor: StandardizationFloor
    rank_clip_epsilon_relative: Epsilon
    zero_displacement_floor: ZeroDisplacementFloor
    projection_tie_tolerance: Tolerance
    condition_number_limit: ConditionNumberLimit
    solver: SolverTolerances


class SignificantFiguresPolicy(StrictModel):
    percentages_and_rates: EpochCount
    raw_action_width_and_alignment: EpochCount
    effect_sizes_and_p_values: EpochCount


class ReportingConfig(StrictModel):
    significant_figures: SignificantFiguresPolicy
    p_value_display_threshold: Epsilon


class WorkspaceDirectories(StrictModel):
    preprocessing: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    shared_artifacts: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    shared_models: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    shared_scores: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    shared_fitted: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    shared_baselines: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    shared_derived: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    experiments: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    cache: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    staging: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    result_experiments: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    project_summary: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    reproducibility: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this


class WorkspaceConfig(StrictModel):
    configuration_file: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    outputs_root: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    results_root: RelativePosixPath #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    directories: WorkspaceDirectories
    experiment_directories: list[ExperimentDirectoryName] #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this


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


class ConfigurationConstraintError(ValueError):
    pass


def _require_membership(
    value: float | int, candidates: list[float] | list[int], label: str
) -> None:
    if value not in candidates:
        raise ConfigurationConstraintError(f"{label} must be one of {candidates}; got {value}")


def _require_relative_descendant(parent: str, child: str, label: str) -> None:
    parent_path = PurePosixPath(parent)
    child_path = PurePosixPath(child)
    if child_path == parent_path or parent_path not in child_path.parents:
        raise ConfigurationConstraintError(
            f"{label} must be a strict relative descendant of {parent}; got {child}"
        )


def _validate_temporal_consistency(config: FedActConfig) -> None:
    horizons = config.temporal.forecast_horizons_months
    if config.temporal.primary_confirmatory_horizon_months not in horizons:
        raise ConfigurationConstraintError(
            "temporal.primary_confirmatory_horizon_months must be a configured forecast horizon"
        )
    if config.temporal.early_horizon_months not in horizons:
        raise ConfigurationConstraintError(
            "temporal.early_horizon_months must be a configured forecast horizon"
        )


def _validate_identification_selections(config: FedActConfig) -> None:
    identification = config.identification
    if identification.nuisance_rank.maximum != max(identification.nuisance_rank.candidates):
        raise ConfigurationConstraintError(
            "identification.nuisance_rank.maximum must equal its largest candidate"
        )
    _require_membership(
        identification.eigengap_ratio.default_without_nested_calibration,
        identification.eigengap_ratio.candidates,
        "identification.eigengap_ratio.default_without_nested_calibration",
    )
    _require_membership(
        identification.target_coverage.primary,
        identification.target_coverage.candidates,
        "identification.target_coverage.primary",
    )
    _require_membership(
        identification.control_span_violation.primary_alpha,
        identification.control_span_violation.sensitivity_alpha,
        "identification.control_span_violation.primary_alpha",
    )
    _require_membership(
        identification.private_contamination.primary_alpha,
        identification.private_contamination.sensitivity_alpha,
        "identification.private_contamination.primary_alpha",
    )
    _require_membership(
        identification.covariance_regularization.primary_c,
        identification.covariance_regularization.sensitivity_c,
        "identification.covariance_regularization.primary_c",
    )


def _validate_hardening_selection(config: FedActConfig) -> None:
    _require_membership(
        config.hardening.maximum_actions_per_sample.primary,
        config.hardening.maximum_actions_per_sample.candidates,
        "hardening.maximum_actions_per_sample.primary",
    )


def _validate_workspace_layout(config: FedActConfig) -> None:
    workspace = config.workspace
    directories = workspace.directories
    outputs_root = workspace.outputs_root
    results_root = workspace.results_root

    _require_relative_descendant(
        outputs_root, directories.preprocessing, "workspace.directories.preprocessing"
    )
    _require_relative_descendant(
        outputs_root, directories.experiments, "workspace.directories.experiments"
    )
    _require_relative_descendant(outputs_root, directories.cache, "workspace.directories.cache")
    _require_relative_descendant(
        directories.cache, directories.staging, "workspace.directories.staging"
    )
    _require_relative_descendant(
        workspace.results_root,
        directories.result_experiments,
        "workspace.directories.result_experiments",
    )
    _require_relative_descendant(
        results_root, directories.project_summary, "workspace.directories.project_summary"
    )
    _require_relative_descendant(
        directories.project_summary,
        directories.reproducibility,
        "workspace.directories.reproducibility",
    )

    shared_children = {
        "shared_models": directories.shared_models,
        "shared_scores": directories.shared_scores,
        "shared_fitted": directories.shared_fitted,
        "shared_baselines": directories.shared_baselines,
        "shared_derived": directories.shared_derived,
    }
    for label, path in shared_children.items():
        _require_relative_descendant(
            directories.shared_artifacts, path, f"workspace.directories.{label}"
        )

    if len(set(workspace.experiment_directories)) != len(workspace.experiment_directories):
        raise ConfigurationConstraintError("workspace.experiment_directories must be unique")
    if any(not name for name in workspace.experiment_directories):
        raise ConfigurationConstraintError(
            "workspace.experiment_directories must contain non-empty names"
        )


def validate_configuration_constraints(config: FedActConfig) -> None:
    _validate_temporal_consistency(config)
    _validate_identification_selections(config)
    _validate_hardening_selection(config)
    _validate_workspace_layout(config)
