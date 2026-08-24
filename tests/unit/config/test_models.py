from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from fedact.config.loading import LoadedConfiguration, load_production_configuration
from fedact.config.models import (
    ConfirmatoryFormat,
    FedActConfig,
    FederationGeometry,
    PrivateTransitionSparsityMode,
)


def test_production_file_matches_roadmap_configuration_block(
    roadmap_configuration_block: str, production_payload: str
) -> None:
    assert production_payload == roadmap_configuration_block


def test_typed_model_preserves_every_roadmap_value_exactly(production_payload: str) -> None:
    authoritative = yaml.safe_load(production_payload)
    assert isinstance(authoritative, dict)
    assert FedActConfig.model_validate(authoritative).model_dump(mode="json") == authoritative


def test_independently_transcribed_dataset_temporal_training_and_identification_values(
    production_configuration_path: Path,
) -> None:
    config = load_production_configuration(production_configuration_path).values

    assert config.datasets.lamda.labels.benign_detection_count == 0
    assert config.datasets.lamda.labels.malware_minimum_detection_count == 4
    assert config.datasets.lamda.labels.discard_detection_counts == [1, 2, 3]
    assert config.datasets.lamda.preprocessing.raw_variance_threshold_when_required == 0.001
    assert config.datasets.ember2024.confirmatory_formats == [
        ConfirmatoryFormat.WIN32_PE,
        ConfirmatoryFormat.WIN64_PE,
    ]

    assert config.temporal.historical_training_window_months == 12
    assert config.temporal.transition_interval_months == 3
    assert config.temporal.cutoff_step_months == 1
    assert config.temporal.full_retraining_interval_months == 3
    assert config.temporal.forecast_horizons_months == [1, 3, 6, 12]
    assert config.temporal.primary_confirmatory_horizon_months == 3
    assert config.temporal.early_horizon_months == 1
    assert config.temporal.temporal_model.minimum_consecutive_pairs == 3
    assert config.temporal.temporal_model.maximum_scalar_coefficient == 0.99
    assert config.temporal.process_noise.quantile == 0.95

    assert config.training.initial_learning_rate == 0.001
    assert config.training.final_learning_rate == 0.00001
    assert config.training.batch_size == 256
    assert config.training.maximum_epochs == 30
    assert config.training.early_stopping_patience_epochs == 5
    assert config.training.validation_fraction == 0.10

    identification = config.identification
    assert identification.minimum_support_per_class == 200
    assert identification.minimum_control_transition_replicates == 3
    assert identification.uncertainty.bootstrap_resamples == 500
    assert identification.nuisance_rank.candidates == list(range(1, 21))
    assert identification.nuisance_rank.maximum == 20
    assert identification.nuisance_rank.bootstrap_resamples == 200
    assert identification.nuisance_rank.minimum_bootstrap_stability_fraction == 0.80
    assert identification.eigengap_ratio.candidates == [1.05, 1.10, 1.25, 1.50, 1.75, 2.00]
    assert identification.eigengap_ratio.default_without_nested_calibration == 1.25
    assert identification.target_coverage.candidates == [0.80, 0.85, 0.90, 0.95]
    assert identification.target_coverage.primary == 0.90
    assert identification.control_span_violation.primary_alpha == 0.05
    assert identification.control_span_violation.sensitivity_alpha == [0.01, 0.05, 0.10, 0.20]
    assert identification.private_contamination.primary_alpha == 0.05
    assert identification.private_contamination.sensitivity_alpha == [0.01, 0.05, 0.10, 0.20]
    assert identification.private_contamination.minimum_history_residuals == 5
    radius = identification.historical_plausibility_radius
    assert radius.center_norm_quantile == 0.95
    assert radius.minimum_reference_centers == 5
    assert radius.sensitivity_multipliers == [0.75, 1.00, 1.50, 2.00]
    regularization = identification.covariance_regularization
    assert regularization.primary_c == 0.01
    assert regularization.sensitivity_c == [0.001, 0.01, 0.05, 0.10]
    gate = identification.control_reconstruction_gate
    assert gate.held_out_residual_quantile == 0.75
    assert gate.minimum_pass_fraction == 0.80
    tail = identification.tail_diagnostic
    assert tail.maximum_absolute_excess_kurtosis == 10.0
    assert tail.maximum_flagged_coordinate_fraction == 0.10


def test_independently_transcribed_certification_operators_hardening_and_robustness_values(
    production_configuration_path: Path,
) -> None:
    config = load_production_configuration(production_configuration_path).values

    certification = config.certification
    assert certification.alignment_threshold.percentile_candidates == [50, 60, 70, 75, 80, 85, 90]
    assert certification.ambiguity_width.percentile_candidates == [50, 60, 70, 75, 80]
    diameter = certification.forecast_set_diameter_abstention
    assert diameter.historical_realized_diameter_quantile == 0.90
    stability = certification.leave_one_client_out_stability
    assert stability.minimum_unchanged_fraction == 0.80
    assert certification.random_matching.minimum_exact_or_source_fraction == 0.80

    assert config.operators.minimum_valid_coverage == 0.50
    assert config.operators.maximum_composed_atomic_actions == 3
    validation = config.operators.validation
    assert validation.execution_timeout_seconds == 60
    assert validation.android_monkey_events == 500
    assert validation.minimum_behavior_jaccard == 0.80

    assert config.ablations.zero_control_span_violation_budget == 0
    assert config.ablations.zero_private_contamination_budget == 0

    hardening = config.hardening
    assert hardening.weight.candidates == [0.1, 0.3, 0.5, 0.7, 0.9, 1.0]
    assert hardening.weight.maximum_clean_fnr_degradation_percentage_points == 2.0
    actions = hardening.maximum_actions_per_sample
    assert actions.candidates == [1, 3, 5, 10]
    assert actions.primary == 5

    assert config.baselines.point_ridge_relative == 0.001

    allowance = config.robustness.corrupted_client_allowance
    assert allowance.counts == [0, 1, 2]
    assert {attack.value for attack in allowance.attacks} == {
        "basis_rotation",
        "false_rank_reporting",
        "beta_under_reporting",
        "transition_poisoning",
        "fabricated_complementarity",
    }
    parameters = allowance.parameters
    assert parameters.basis_rotation_degrees == 30
    assert parameters.false_rank_increment == 2
    assert parameters.beta_multiplier == 0.50
    assert parameters.transition_poisoning_sigma == 2.0
    assert parameters.fabricated_complementarity_rotation_degrees == 45
    stress = config.robustness.real_stress
    assert stress.control_support_fractions == [0.75, 0.50, 0.25]
    assert stress.control_transition_noise_sigma_multipliers == [0.25, 0.50, 1.0]


def test_independently_transcribed_statistics_seeds_and_analysis_values(
    production_configuration_path: Path,
) -> None:
    config = load_production_configuration(production_configuration_path).values

    statistics = config.statistics
    assert statistics.confidence_level == 0.95
    assert statistics.minimum_paired_cutoffs == 6
    assert statistics.maximum_missing_cutoff_fraction == 0.10
    assert statistics.bootstrap.resamples == 10000
    assert statistics.wilcoxon.maximum_nonzero_pairs_for_exact == 25
    assert statistics.multiplicity.q == 0.05
    effects = statistics.minimum_material_effects
    assert effects.early_horizon_fnr_absolute_reduction_percentage_points == 2.0
    assert effects.action_certification_precision_absolute_increase == 0.05
    assert effects.maximum_coverage_deficit_absolute == 0.02

    seeds = config.seeds
    assert seeds.representation == list(range(1001, 1011))
    assert seeds.detector_training == list(range(2001, 2011))
    assert seeds.synthetic_generation == list(range(3001, 3011))
    assert seeds.synthetic_noise == list(range(4001, 4011))
    assert seeds.operator == list(range(5001, 5011))
    assert seeds.calibration == list(range(6001, 6011))
    assert seeds.baseline == list(range(7001, 7011))
    assert seeds.analysis == list(range(8001, 8011))
    assert seeds.client_selection == list(range(9001, 9011))

    assert config.client_selection.budget_fractions == [0.25, 0.50, 0.75]
    assert config.client_selection.d_optimal_ridge == 1.0e-6

    numerical = config.numerical
    assert numerical.scale_standardization_floor == 1.0e-8
    assert numerical.rank_clip_epsilon_relative == 1.0e-6
    assert numerical.zero_displacement_floor == 1.0e-10
    assert numerical.projection_tie_tolerance == 1.0e-9
    assert numerical.condition_number_limit == 1.0e8
    solver = numerical.solver
    assert solver.relative_tolerance == 1.0e-8
    assert solver.absolute_tolerance == 1.0e-8
    assert solver.duality_gap_tolerance == 1.0e-8
    assert solver.maximum_iterations == 200

    reporting = config.reporting
    assert reporting.significant_figures.percentages_and_rates == 3
    assert reporting.significant_figures.raw_action_width_and_alignment == 4
    assert reporting.significant_figures.effect_sizes_and_p_values == 3
    assert reporting.p_value_display_threshold == 1.0e-4


def test_independently_transcribed_synthetic_and_artifact_values(
    production_configuration_path: Path,
) -> None:
    config = load_production_configuration(production_configuration_path).values

    synthetic = config.synthetic
    assert synthetic.base_sigma == 1.0
    assert synthetic.shared_transition_norm_over_sigma == 1.0
    assert synthetic.independent_draws_per_grid_cell == 30
    assert synthetic.nested_noise_draws_per_seed == 3
    defaults = synthetic.defaults
    assert defaults.nuisance_dimension_fraction == 0.30
    assert defaults.control_malicious_amplitude_ratio == 1.0
    assert defaults.pairwise_principal_angle_degrees == 45
    assert defaults.common_intersection_dimension == 2
    assert defaults.federation_client_count == 3
    assert defaults.federation_geometry is FederationGeometry.COMPLEMENTARY
    assert defaults.control_sample_size == 200
    assert defaults.malicious_sample_size == 100
    assert defaults.control_span_violation_over_sigma == 0.10
    assert defaults.synchronized_nuisance_over_sigma == 0.0
    assert defaults.private_transition_norm_over_sigma == 0.25
    assert defaults.private_transition_sparsity_mode is PrivateTransitionSparsityMode.DENSE
    assert defaults.outlier_client_count == 0
    assert defaults.spectral_conditioning_ratio == 0.10
    assert defaults.action_rotation_angle_degrees == 30
    sweeps = synthetic.sweeps
    assert sweeps.nuisance_dimension.fractions == [0.05, 0.15, 0.30, 0.50, 0.70]
    assert sweeps.control_malicious_amplitude_ratio == [0.25, 0.50, 1.0, 2.0, 4.0]
    assert sweeps.pairwise_principal_angle_degrees == [0, 15, 30, 45, 60, 90]
    assert sweeps.common_intersection_dimension == [0, 2, 5, 10]
    assert sweeps.federation.client_counts == [2, 3, 5, 8]
    assert sweeps.federation.geometries == [
        FederationGeometry.REDUNDANT,
        FederationGeometry.COMPLEMENTARY,
    ]
    assert sweeps.federation.matched_total_samples is True
    assert sweeps.control_sample_size == [50, 100, 200, 500, 1000]
    assert sweeps.malicious_sample_size == [20, 50, 100, 200, 500]
    assert sweeps.control_span_violation_over_sigma == [0, 0.10, 0.25, 0.50, 1.0]
    assert sweeps.synchronized_nuisance_over_sigma == [0, 0.25, 0.50, 1.0, 2.0]
    private = sweeps.private_transition
    assert private.norm_over_sigma == [0, 0.25, 0.50, 1.0, 2.0]
    assert private.sparsity_modes == [
        PrivateTransitionSparsityMode.DENSE,
        PrivateTransitionSparsityMode.TEN_PERCENT_SPARSE,
    ]
    assert private.sparse_fraction == 0.10
    outlier = sweeps.outlier_client_stress
    assert outlier.corrupted_client_counts == [0, 1, 2]
    assert {attack.value for attack in outlier.attacks} == {
        "rotation",
        "rank_misreport",
        "beta_underreport",
        "poisoning",
        "fabricated_complementarity",
    }
    assert sweeps.spectral_conditioning_ratio == [0.01, 0.05, 0.10, 0.50, 1.0]
    assert sweeps.action_rotation_angle_degrees == [0, 15, 30, 45, 60, 75, 90]

    artifacts = config.artifacts
    assert artifacts.configuration_file == "configs/fedact.yaml"
    assert artifacts.outputs_root == "outputs"
    assert artifacts.results_root == "results"
    directories = artifacts.directories
    assert directories.preprocessing == "outputs/preprocessing"
    assert directories.shared_artifacts == "outputs/artifacts"
    assert directories.shared_models == "outputs/artifacts/models"
    assert directories.shared_scores == "outputs/artifacts/scores"
    assert directories.shared_fitted == "outputs/artifacts/fitted"
    assert directories.shared_baselines == "outputs/artifacts/baselines"
    assert directories.shared_derived == "outputs/artifacts/derived"
    assert directories.shared_provenance == "outputs/artifacts/provenance"
    assert directories.experiments == "outputs/experiments"
    assert directories.cache == "outputs/cache"
    assert directories.staging == "outputs/cache/staging"
    assert directories.result_experiments == "results/experiments"
    assert directories.project_summary == "results/project_summary"
    assert directories.reproducibility == "results/project_summary/reproducibility"
    assert artifacts.experiment_directories == [
        "math-verification",
        "synthetic-geometry",
        "action-certificate-validation",
        "prospective-evaluation",
        "ablations",
        "federation",
        "failure-boundaries",
        "cross-corpus",
        "client-selection",
        "statistical-synthesis",
    ]
    assert artifacts.result_payload_directories == ["figures", "tables", "metrics", "statistics"]
    assert (
        artifacts.active_artifact_index
        == "outputs/artifacts/provenance/indexes/artifact_index.jsonl"
    )
    assert (
        artifacts.dependency_index == "outputs/artifacts/provenance/indexes/dependency_index.json"
    )
    assert (
        artifacts.evidence_index
        == "results/project_summary/reproducibility/execution/evidence_index.json"
    )


def test_unknown_fields_are_rejected(production_payload: str) -> None:
    mutated = production_payload.replace(
        "datasets:", "datasets:\n  unexpected_section:\n    value: 1", 1
    )
    raw_data = yaml.safe_load(mutated)
    with pytest.raises(ValidationError):
        FedActConfig.model_validate(raw_data)


def test_out_of_range_values_are_rejected(production_payload: str) -> None:
    mutated = production_payload.replace("confidence_level: 0.95", "confidence_level: 1.5", 1)
    raw_data = yaml.safe_load(mutated)
    with pytest.raises(ValidationError):
        FedActConfig.model_validate(raw_data)


def test_wrong_scalar_types_are_rejected(production_payload: str) -> None:
    mutated = production_payload.replace("batch_size: 256", "batch_size: many", 1)
    raw_data = yaml.safe_load(mutated)
    with pytest.raises(ValidationError):
        FedActConfig.model_validate(raw_data)


def test_unknown_enum_tokens_are_rejected(production_payload: str) -> None:
    mutated = production_payload.replace(
        "confirmatory_formats: [win32_pe, win64_pe]",
        "confirmatory_formats: [win32_pe, win128_pe]",
        1,
    )
    raw_data = yaml.safe_load(mutated)
    with pytest.raises(ValidationError):
        FedActConfig.model_validate(raw_data)


def test_frozen_models_reject_mutation(production_configuration: LoadedConfiguration) -> None:
    with pytest.raises(ValidationError):
        production_configuration.values.training.batch_size = 128
