from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from fedact.config.loading import load_production_configuration
from fedact.config.models import FedActConfig
from fedact.config.validation import (
    ConfigurationConstraintError,
    validate_configuration_constraints,
)


def mutated_configuration(production_payload: str, old: str, new: str) -> FedActConfig:
    assert old in production_payload, f"mutation target missing from production payload: {old}"
    mutated_payload = production_payload.replace(old, new, 1)
    raw = yaml.safe_load(mutated_payload)
    assert isinstance(raw, dict)
    return FedActConfig.model_validate(raw)


def test_primary_confirmatory_horizon_must_be_a_configured_forecast_horizon(
    production_payload: str,
) -> None:
    config = mutated_configuration(
        production_payload,
        "primary_confirmatory_horizon_months: 3",
        "primary_confirmatory_horizon_months: 5",
    )
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_early_horizon_must_be_a_configured_forecast_horizon(production_payload: str) -> None:
    config = mutated_configuration(
        production_payload, "early_horizon_months: 1", "early_horizon_months: 2"
    )
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_nuisance_rank_maximum_must_equal_largest_candidate(production_payload: str) -> None:
    config = mutated_configuration(production_payload, "maximum: 20", "maximum: 19")
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_eigengap_default_must_be_an_available_candidate(production_payload: str) -> None:
    config = mutated_configuration(
        production_payload,
        "default_without_nested_calibration: 1.25",
        "default_without_nested_calibration: 1.30",
    )
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_target_coverage_primary_must_be_an_available_candidate(production_payload: str) -> None:
    config = mutated_configuration(
        production_payload,
        "candidates: [0.80, 0.85, 0.90, 0.95]\n    primary: 0.90",
        "candidates: [0.80, 0.85, 0.90, 0.95]\n    primary: 0.99",
    )
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_control_span_primary_alpha_must_be_inside_sensitivity_grid(
    production_payload: str,
) -> None:
    control_span_block = (
        "control_span_violation:\n"
        "    primary_alpha: 0.05\n"
        "    sensitivity_alpha: [0.01, 0.05, 0.10, 0.20]"
    )
    mutated_control_span_block = (
        "control_span_violation:\n"
        "    primary_alpha: 0.02\n"
        "    sensitivity_alpha: [0.01, 0.05, 0.10, 0.20]"
    )
    config = mutated_configuration(
        production_payload,
        control_span_block,
        mutated_control_span_block,
    )
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_private_contamination_primary_alpha_must_be_inside_sensitivity_grid(
    production_payload: str,
) -> None:
    config = mutated_configuration(
        production_payload,
        "private_contamination:\n    primary_alpha: 0.05",
        "private_contamination:\n    primary_alpha: 0.07",
    )
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_covariance_regularization_primary_c_must_be_inside_sensitivity_grid(
    production_payload: str,
) -> None:
    config = mutated_configuration(
        production_payload,
        "covariance_regularization:\n    primary_c: 0.01",
        "covariance_regularization:\n    primary_c: 0.02",
    )
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_maximum_actions_per_sample_primary_must_be_an_available_candidate(
    production_payload: str,
) -> None:
    config = mutated_configuration(
        production_payload,
        "maximum_actions_per_sample:\n    candidates: [1, 3, 5, 10]\n    primary: 5",
        "maximum_actions_per_sample:\n    candidates: [1, 3, 5, 10]\n    primary: 7",
    )
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_staging_directory_must_live_under_cache(production_payload: str) -> None:
    config = mutated_configuration(
        production_payload, "staging: outputs/cache/staging", "staging: outputs/staging"
    )
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_shared_subdirectories_must_live_under_shared_artifacts(production_payload: str) -> None:
    config = mutated_configuration(
        production_payload,
        "shared_models: outputs/artifacts/models",
        "shared_models: outputs/models",
    )
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_active_artifact_index_must_live_under_shared_provenance(production_payload: str) -> None:
    config = mutated_configuration(
        production_payload,
        "active_artifact_index: outputs/artifacts/provenance/indexes/artifact_index.jsonl",
        "active_artifact_index: outputs/indexes/artifact_index.jsonl",
    )
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_evidence_index_must_live_under_reproducibility(production_payload: str) -> None:
    config = mutated_configuration(
        production_payload,
        "evidence_index: results/project_summary/reproducibility/execution/evidence_index.json",
        "evidence_index: results/project_summary/execution/evidence_index.json",
    )
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_result_directories_must_live_under_results_root(production_payload: str) -> None:
    config = mutated_configuration(
        production_payload,
        "project_summary: results/project_summary",
        "project_summary: outputs/project_summary",
    )
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_experiment_directories_must_be_unique(production_payload: str) -> None:
    config = mutated_configuration(
        production_payload,
        "- math-verification\n    - synthetic-geometry",
        "- math-verification\n    - math-verification",
    )
    with pytest.raises(ConfigurationConstraintError):
        validate_configuration_constraints(config)


def test_production_configuration_passes_all_constraints(
    production_configuration_path: Path,
) -> None:
    loaded = load_production_configuration(production_configuration_path)
    validate_configuration_constraints(loaded.values)
