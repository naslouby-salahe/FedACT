from __future__ import annotations

from fedact.analysis.metrics import EvaluationRecord, compute_evaluation_metrics
from fedact.domain.types import DatasetSelector, SampleIdentifier, SplitCutoffIdentity


def test_compute_evaluation_metrics() -> None:
    records = (
        EvaluationRecord(
            dataset=DatasetSelector.LAMDA,
            cutoff_id=SplitCutoffIdentity("cutoff_01"),
            sample_id=SampleIdentifier("s1"),
            horizon_step=1,
            true_label=True,
            predicted_score=0.9,
            is_certified=True,
            clean_loss=0.1,
        ),
        EvaluationRecord(
            dataset=DatasetSelector.LAMDA,
            cutoff_id=SplitCutoffIdentity("cutoff_01"),
            sample_id=SampleIdentifier("s2"),
            horizon_step=1,
            true_label=False,
            predicted_score=0.1,
            is_certified=False,
            clean_loss=0.05,
        ),
    )
    metrics = compute_evaluation_metrics(records)
    assert metrics.false_negative_rate == 0.0
    assert metrics.certification_rate == 0.5
    assert metrics.true_positive_rate == 1.0
    assert metrics.false_positive_rate == 0.0
    assert metrics.abstention_rate == 0.5
    assert metrics.pr_auc == 1.0
    assert metrics.roc_auc == 1.0


def test_compute_evaluation_metrics_auc_is_none_without_both_classes() -> None:
    records = (
        EvaluationRecord(
            dataset=DatasetSelector.LAMDA,
            cutoff_id=SplitCutoffIdentity("cutoff_01"),
            sample_id=SampleIdentifier("s1"),
            horizon_step=1,
            true_label=True,
            predicted_score=0.9,
            is_certified=True,
            clean_loss=0.1,
        ),
    )
    metrics = compute_evaluation_metrics(records)
    assert metrics.pr_auc is None
    assert metrics.roc_auc is None
