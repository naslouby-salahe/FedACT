from __future__ import annotations

from fedact.evaluation.metrics import EvaluationMetrics
from fedact.evaluation.validation import validate_evaluation_metrics


def test_validate_evaluation_metrics() -> None:
    m = EvaluationMetrics(
        false_negative_rate=0.1,
        certification_rate=0.8,
        clean_fnr=0.05,
        cumulative_exposure=1.2,
    )
    validate_evaluation_metrics(m)
