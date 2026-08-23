from __future__ import annotations

from fedact.domain.enums import DatasetSelector
from fedact.domain.records import SampleIdentifier, SplitCutoffIdentity
from fedact.evaluation.metrics import compute_evaluation_metrics
from fedact.evaluation.records import EvaluationRecord


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
