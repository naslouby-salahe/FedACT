from __future__ import annotations

from fedact.evaluation.metrics import EvaluationMetrics


class MetricValidationError(ValueError):
    pass


def validate_evaluation_metrics(metrics: EvaluationMetrics) -> None:
    if not (0.0 <= metrics.false_negative_rate <= 1.0):
        raise MetricValidationError("false negative rate out of bounds [0, 1]")
    if not (0.0 <= metrics.certification_rate <= 1.0):
        raise MetricValidationError("certification rate out of bounds [0, 1]")
