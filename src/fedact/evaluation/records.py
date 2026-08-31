from __future__ import annotations

from dataclasses import dataclass

from fedact.domain.enums import DatasetSelector
from fedact.domain.records import (
    BinaryLabel,
    HorizonStep,
    LossValue,
    ProbabilityValue,
    SampleIdentifier,
    SplitCutoffIdentity,
)


@dataclass(frozen=True)
class EvaluationRecord:
    dataset: DatasetSelector
    cutoff_id: SplitCutoffIdentity
    sample_id: SampleIdentifier
    horizon_step: HorizonStep
    true_label: BinaryLabel
    predicted_score: ProbabilityValue
    is_certified: bool
    clean_loss: LossValue
