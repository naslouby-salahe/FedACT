from __future__ import annotations

from pathlib import PurePosixPath

from fedact.config.models import FedActConfig


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
        "shared_provenance": directories.shared_provenance,
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
