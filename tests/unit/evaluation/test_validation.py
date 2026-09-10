from __future__ import annotations

from fedact.analysis.metrics import EvaluationMetrics, validate_evaluation_metrics


def test_validate_evaluation_metrics() -> None:
    m = EvaluationMetrics(
        false_negative_rate=0.1,
        certification_rate=0.8,
        clean_fnr=0.05,
        cumulative_exposure=1.2,
        true_positive_rate=0.9,
        false_positive_rate=0.05,
        abstention_rate=0.2,
    )
    validate_evaluation_metrics(m)
