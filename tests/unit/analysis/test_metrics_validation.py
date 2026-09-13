from __future__ import annotations

import dataclasses

import pytest

from fedact.analysis.metrics import (
    EvaluationMetrics,
    MetricValidationError,
    validate_evaluation_metrics,
)

VALID_METRICS = EvaluationMetrics(
    false_negative_rate=0.2,
    certification_rate=0.8,
    clean_fnr=0.1,
    cumulative_exposure=0.3,
    true_positive_rate=0.9,
    false_positive_rate=0.05,
    abstention_rate=0.1,
    pr_auc=0.7,
    roc_auc=0.75,
)
OUT_OF_BOUNDS = 1.5


def test_valid_metrics_pass_validation() -> None:
    validate_evaluation_metrics(VALID_METRICS)


@pytest.mark.parametrize(
    ("field", "message"),
    [
        ("false_negative_rate", "false negative rate out of bounds"),
        ("certification_rate", "certification rate out of bounds"),
        ("true_positive_rate", "true positive rate out of bounds"),
        ("false_positive_rate", "false positive rate out of bounds"),
        ("abstention_rate", "abstention rate out of bounds"),
        ("pr_auc", "PR-AUC out of bounds"),
        ("roc_auc", "ROC-AUC out of bounds"),
    ],
)
def test_out_of_bounds_metric_is_rejected(field: str, message: str) -> None:
    invalid = dataclasses.replace(VALID_METRICS, **{field: OUT_OF_BOUNDS})
    with pytest.raises(MetricValidationError, match=message):
        validate_evaluation_metrics(invalid)


def test_absent_auc_metrics_are_not_validated() -> None:
    without_auc = dataclasses.replace(VALID_METRICS, pr_auc=None, roc_auc=None)
    validate_evaluation_metrics(without_auc)
