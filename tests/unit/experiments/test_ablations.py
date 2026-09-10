from __future__ import annotations

import json
from pathlib import Path

import pytest

from fedact.domain.types import ScientificOutcome
from fedact.experiments.robustness import run_novelty_critical_ablations
from fedact.workflow import Application


def test_ablation_requires_completed_prospective_evidence(application: Application) -> None:
    report = run_novelty_critical_ablations(application)
    assert report.evaluated_configurations == 0
    assert report.scientific_outcome is ScientificOutcome.INSUFFICIENT_EVIDENCE


@pytest.fixture
def isolated_application(tmp_path: Path, application: Application) -> Application:
    return Application(repository_root=tmp_path, configuration=application.configuration)


def test_hardening_off_ablation_measures_real_degradation(
    isolated_application: Application,
) -> None:
    destination = (
        isolated_application.repository_root
        / isolated_application.configuration.values.workspace.directories.experiments
        / "prospective-evaluation"
        / "cutoff-comparisons.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "comparisons": [
                    {
                        "cutoff_id": "lamda-1",
                        "hardened_false_negative_rate": 0.1,
                        "static_chronological_false_negative_rate": 0.4,
                    },
                    {
                        "cutoff_id": "lamda-2",
                        "hardened_false_negative_rate": 0.2,
                        "static_chronological_false_negative_rate": 0.5,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    report = run_novelty_critical_ablations(isolated_application)
    assert report.evaluated_configurations == 1
    assert report.scientific_outcome is ScientificOutcome.PASS
    result = report.results[0]
    assert result.ablation_name == "hardening_off"
    assert result.degradation_percentage_points == pytest.approx(30.0)


def test_point_vs_set_ablation_measures_real_precision_gap(
    isolated_application: Application,
) -> None:
    destination = (
        isolated_application.repository_root
        / isolated_application.configuration.values.workspace.directories.experiments
        / "action-certificate-validation"
        / "central-pattern.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "cutoffs": [
                    {
                        "cutoff_id": "lamda-1",
                        "certified_precision": 0.9,
                        "point_selected_precision": 0.5,
                        "matched_random_precision": 0.2,
                        "matched_random_match_quality_sufficient": True,
                    },
                    {
                        "cutoff_id": "lamda-2",
                        "certified_precision": 0.8,
                        "point_selected_precision": 0.4,
                        "matched_random_precision": 0.1,
                        "matched_random_match_quality_sufficient": True,
                    },
                ],
                "rank_alignment_spearman_rho": 0.6,
            }
        ),
        encoding="utf-8",
    )
    report = run_novelty_critical_ablations(isolated_application)
    assert report.evaluated_configurations == 1
    assert report.scientific_outcome is ScientificOutcome.PASS
    result = report.results[0]
    assert result.ablation_name == "point_vs_set"
    assert result.degradation_percentage_points == pytest.approx(40.0)


def test_identification_derived_ablations_measure_real_beta_deltas(
    isolated_application: Application,
) -> None:
    destination = (
        isolated_application.repository_root
        / isolated_application.configuration.values.workspace.directories.experiments
        / "prospective-evaluation"
        / "identification-diagnostics.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "cohort": "smsreg",
                "cutoffs": [
                    {
                        "cutoff": 121,
                        "cohort": "smsreg",
                        "fitted": True,
                        "beta": 0.2,
                        "no_controls_beta": 0.5,
                        "one_matched_control_beta": 0.4,
                        "zero_subspace_term_beta": 0.15,
                        "zero_control_span_term_beta": 0.18,
                        "zero_private_term_beta": 0.1,
                    },
                    {
                        "cutoff": 122,
                        "cohort": "smsreg",
                        "fitted": True,
                        "beta": 0.3,
                        "no_controls_beta": 0.6,
                        "one_matched_control_beta": 0.5,
                        "zero_subspace_term_beta": 0.25,
                        "zero_control_span_term_beta": 0.28,
                        "zero_private_term_beta": 0.2,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    report = run_novelty_critical_ablations(isolated_application)
    assert report.evaluated_configurations == 5
    assert report.scientific_outcome is ScientificOutcome.PASS
    by_name = {result.ablation_name: result for result in report.results}
    assert by_name["no_controls"].degradation_percentage_points == pytest.approx(30.0)
    assert by_name["one_matched_control"].degradation_percentage_points == pytest.approx(20.0)
    assert by_name["zero_subspace_uncertainty_term"].degradation_percentage_points == pytest.approx(
        -5.0
    )
    assert by_name[
        "zero_control_span_allowance_term"
    ].degradation_percentage_points == pytest.approx(-2.0)
    assert by_name[
        "zero_private_transition_allowance_term"
    ].degradation_percentage_points == pytest.approx(-10.0)


def test_temporal_dynamics_ablations_measure_real_process_error_deltas(
    isolated_application: Application,
) -> None:
    destination = (
        isolated_application.repository_root
        / isolated_application.configuration.values.workspace.directories.experiments
        / "ablations"
        / "temporal-dynamics.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "endpoints_used": 10,
                "baseline_coefficient": 0.5,
                "baseline_process_error": 0.2,
                "shuffled_history_process_error": 0.5,
                "no_change_dynamics_process_error": 0.35,
            }
        ),
        encoding="utf-8",
    )
    report = run_novelty_critical_ablations(isolated_application)
    assert report.evaluated_configurations == 2
    assert report.scientific_outcome is ScientificOutcome.INSUFFICIENT_EVIDENCE
    by_name = {result.ablation_name: result for result in report.results}
    assert by_name["shuffled_history"].degradation_percentage_points == pytest.approx(30.0)
    assert by_name["no_change_dynamics"].degradation_percentage_points == pytest.approx(15.0)
