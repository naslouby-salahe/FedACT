from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import torch

from fedact.config.loading import LoadedConfiguration
from fedact.core.controls import (
    ControlQualityGate,
    ControlReplicate,
    filter_control_replicates,
)
from fedact.core.nuisance import (
    admissible_rank,
    eigengap_ratio,
    regularized_covariance,
    select_rank_by_eigengap,
    weighted_covariance,
)
from fedact.datasets.chronology import calendar_month
from fedact.datasets.lamda.loader import load_lamda_records
from fedact.datasets.lamda.semantics import (
    control_transition_replicates,
    label_derivation_rule,
    malicious_transition_displacement,
    replicate_weights,
    year_month_to_calendar_month,
)

LAMDA_BASELINE_DIRECTORY = (
    Path(__file__).resolve().parents[3] / "data" / "raw" / "LAMDA" / "Baseline"
)

pytestmark = pytest.mark.skipif(
    not LAMDA_BASELINE_DIRECTORY.is_dir(), reason="data/raw/LAMDA/Baseline is not available"
)


def test_real_lamda_control_transitions_drive_a_genuine_nuisance_estimate(
    production_configuration: LoadedConfiguration,
) -> None:
    config = production_configuration.values
    dataset = load_lamda_records(LAMDA_BASELINE_DIRECTORY / "2023")
    assert len(dataset.records) > 0
    rule = label_derivation_rule(config.datasets.lamda)

    transition_interval_months = config.temporal.transition_interval_months
    cutoff_endpoint = year_month_to_calendar_month("2023-11")

    malicious_signal = malicious_transition_displacement(
        dataset.records, dataset.features, rule, cutoff_endpoint, transition_interval_months
    )
    assert malicious_signal is not None
    assert malicious_signal.support_before >= config.identification.minimum_support_per_class
    assert malicious_signal.support_after >= config.identification.minimum_support_per_class
    assert not np.allclose(malicious_signal.displacement, 0.0)

    historical_endpoints = [
        calendar_month(month) for month in range(int(cutoff_endpoint) - 6, int(cutoff_endpoint))
    ]
    replicates = control_transition_replicates(
        dataset.records, dataset.features, rule, historical_endpoints, transition_interval_months
    )
    assert len(replicates) >= config.identification.minimum_control_transition_replicates
    for replicate in replicates:
        assert replicate.support_before >= config.identification.minimum_support_per_class
        assert replicate.support_after >= config.identification.minimum_support_per_class

    weights = replicate_weights(replicates)
    assert len(weights) == len(replicates)
    assert sum(weights) == pytest.approx(1.0)

    control_replicates = [
        ControlReplicate(
            replicate_index=index,
            displacement=torch.tensor(replicate.displacement, dtype=torch.float32),
            support_before=replicate.support_before,
            support_after=replicate.support_after,
        )
        for index, replicate in enumerate(replicates)
    ]
    gate = ControlQualityGate(
        held_out_residual_quantile=config.identification.control_reconstruction_gate.held_out_residual_quantile,
        minimum_pass_fraction=config.identification.control_reconstruction_gate.minimum_pass_fraction,
    )
    passing_replicates = filter_control_replicates(control_replicates, gate)
    assert len(passing_replicates) > 0

    displacements = np.stack([np.array(replicate.displacement) for replicate in replicates])
    weighted_mean = np.average(displacements, axis=0, weights=weights)
    covariance_raw = weighted_covariance(displacements - weighted_mean, weights=weights)
    covariance = regularized_covariance(
        covariance_raw,
        coefficient=config.numerical.rank_clip_epsilon_relative,
        floor=config.numerical.scale_standardization_floor,
    )
    eigenvalues, _ = np.linalg.eigh(covariance)
    eigenvalues = np.sort(eigenvalues)[::-1]

    d = displacements.shape[1]
    r_max_data = admissible_rank(
        dimension=d,
        replicates=len(replicates),
        configured_maximum=config.identification.nuisance_rank.maximum,
    )
    selected_rank = select_rank_by_eigengap(
        eigenvalues,
        maximum_admissible=r_max_data,
        calibrated_requirement=config.identification.eigengap_ratio.default_without_nested_calibration,
        clip_relative=config.numerical.rank_clip_epsilon_relative,
        floor=config.numerical.scale_standardization_floor,
    )
    assert 1 <= selected_rank <= r_max_data

    ratio = eigengap_ratio(
        eigenvalues,
        rank=selected_rank,
        clip_relative=config.numerical.rank_clip_epsilon_relative,
        floor=config.numerical.scale_standardization_floor,
    )
    assert ratio > 0.0
