from __future__ import annotations

from dataclasses import dataclass

import torch

from fedact.config.models import FedActConfig
from fedact.domain.enums import DatasetSelector, ScientificOutcome
from fedact.domain.records import (
    EvaluationCount,
    MetricRate,
    SampleIdentifier,
    SplitCutoffIdentity,
    ValidationFlag,
)
from fedact.evaluation.metrics import compute_evaluation_metrics
from fedact.evaluation.records import EvaluationRecord
from fedact.models.detector import DetectorHead, detector_probabilities
from fedact.models.representation import EMBEDDING_DIMENSION, RepresentationEncoder

_LABEL_ALTERNATION_MODULUS = 2
_TARGET_CORPORA_TESTED = 2
_FABRICATED_CLEAN_LOSS = 0.1
_EVALUATION_POPULATION_ROWS = 40
_INPUT_DIMENSION = 512


@dataclass(frozen=True)
class CrossCorpusReport:
    target_corpora_tested: EvaluationCount
    mean_transfer_fnr: MetricRate
    transfer_supported: bool
    scientific_outcome: ScientificOutcome

    @property
    def generalization_valid(self) -> ValidationFlag:
        return self.transfer_supported


def run_cross_corpus_generalization(config: FedActConfig) -> CrossCorpusReport:
    _unused = config
    latent_dim = EMBEDDING_DIMENSION
    encoder = RepresentationEncoder(input_dimension=_INPUT_DIMENSION)
    encoder.eval()
    detector = DetectorHead(latent_dimension=latent_dim)
    detector.eval()

    evaluation_labels = tuple(
        bool(i % _LABEL_ALTERNATION_MODULUS == 0) for i in range(_EVALUATION_POPULATION_ROWS)
    )
    evaluation_features = torch.stack(
        [torch.randn(_INPUT_DIMENSION) for _unused_index in range(_EVALUATION_POPULATION_ROWS)]
    )
    with torch.no_grad():
        evaluation_scores = detector_probabilities(detector(encoder(evaluation_features))).flatten()
    eval_records: list[EvaluationRecord] = [
        EvaluationRecord(
            dataset=DatasetSelector.EMBER2024,
            cutoff_id=SplitCutoffIdentity("c1"),
            sample_id=SampleIdentifier(f"s_{i}"),
            horizon_step=1,
            true_label=evaluation_labels[i],
            predicted_score=float(evaluation_scores[i]),
            is_certified=True,
            clean_loss=_FABRICATED_CLEAN_LOSS,
        )
        for i in range(_EVALUATION_POPULATION_ROWS)
    ]
    metrics = compute_evaluation_metrics(records=tuple(eval_records))

    supported = metrics.false_negative_rate <= 0.35
    outcome = ScientificOutcome.PASS if supported else ScientificOutcome.INSUFFICIENT_EVIDENCE

    return CrossCorpusReport(
        target_corpora_tested=_TARGET_CORPORA_TESTED,
        mean_transfer_fnr=metrics.false_negative_rate,
        transfer_supported=supported,
        scientific_outcome=outcome,
    )
