from __future__ import annotations

from dataclasses import dataclass

from fedact.domain.enums import DatasetSelector
from fedact.domain.records import SampleIdentifier, SplitCutoffIdentity


@dataclass(frozen=True)
class EvaluationRecord:
    dataset: DatasetSelector
    cutoff_id: SplitCutoffIdentity
    sample_id: SampleIdentifier
    horizon_step: int
    true_label: bool
    predicted_score: float
    is_certified: bool
    clean_loss: float
