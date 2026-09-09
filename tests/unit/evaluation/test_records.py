from __future__ import annotations

from fedact.analysis.metrics import EvaluationRecord
from fedact.domain.types import DatasetSelector, SampleIdentifier, SplitCutoffIdentity


def test_evaluation_record_creation() -> None:
    rec = EvaluationRecord(
        dataset=DatasetSelector.LAMDA,
        cutoff_id=SplitCutoffIdentity("cutoff_01"),
        sample_id=SampleIdentifier("s1"),
        horizon_step=1,
        true_label=True,
        predicted_score=0.95,
        is_certified=True,
        clean_loss=0.05,
    )
    assert rec.true_label
    assert rec.is_certified
