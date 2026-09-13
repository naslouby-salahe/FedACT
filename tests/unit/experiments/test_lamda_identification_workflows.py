from __future__ import annotations

from fedact.domain.types import ScientificOutcome
from fedact.experiments.identification import (
    run_lamda_allowance_sensitivity_stress,
    run_lamda_identification_diagnostics,
    run_lamda_sparse_control_stress,
    run_lamda_temporal_dynamics_ablation,
    run_lamda_weak_eigengap_stress,
)
from fedact.workflow import Application

DOMINANT_FAMILY = "berbew"


def test_identification_diagnostics_selects_the_dominant_cohort_and_evaluates_cutoffs(
    lamda_corpus_application: Application,
) -> None:
    report = run_lamda_identification_diagnostics(lamda_corpus_application)
    assert report.cohort == DOMINANT_FAMILY
    assert report.cutoffs_evaluated > 0
    assert report.cutoffs_fitted >= 0
    assert report.cutoffs_fitted <= report.cutoffs_evaluated
    assert report.scientific_outcome in set(ScientificOutcome)


def test_weak_eigengap_stress_reports_a_bounded_endpoint_and_outcome(
    lamda_corpus_application: Application,
) -> None:
    report = run_lamda_weak_eigengap_stress(lamda_corpus_application)
    assert report.scientific_outcome in set(ScientificOutcome)
    assert report.endpoint is None or report.endpoint >= 0
    assert all(
        record.baseline_selected_rank >= 1 and record.sigma_multiplier > 0
        for record in report.results
    )


def test_sparse_control_stress_reports_an_outcome_even_without_a_baseline_fit(
    lamda_corpus_application: Application,
) -> None:
    report = run_lamda_sparse_control_stress(lamda_corpus_application)
    assert report.scientific_outcome in set(ScientificOutcome)


def test_allowance_sensitivity_stress_keeps_span_and_contamination_results_separate(
    lamda_corpus_application: Application,
) -> None:
    report = run_lamda_allowance_sensitivity_stress(lamda_corpus_application)
    assert report.scientific_outcome in set(ScientificOutcome)
    assert isinstance(report.control_span_results, tuple)
    assert isinstance(report.private_contamination_results, tuple)


def test_temporal_dynamics_ablation_reports_an_explicit_outcome(
    lamda_corpus_application: Application,
) -> None:
    report = run_lamda_temporal_dynamics_ablation(lamda_corpus_application)
    assert report.scientific_outcome in set(ScientificOutcome)
    if report.result is not None:
        assert report.result.endpoints_used >= 1
        assert report.result.baseline_coefficient > 0.0
