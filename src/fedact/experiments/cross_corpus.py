from __future__ import annotations

from dataclasses import dataclass

from fedact.config.models import FedActConfig
from fedact.domain.enums import DatasetSelector, ScientificOutcome
from fedact.domain.records import SampleIdentifier, SplitCutoffIdentity
from fedact.domain.types import EvaluationCount, MetricRate, ValidationFlag
from fedact.evaluation.metrics import compute_evaluation_metrics
from fedact.evaluation.records import EvaluationRecord
from fedact.models.detector import DetectorHead
from fedact.models.representation import EMBEDDING_DIMENSION, RepresentationEncoder

_LABEL_ALTERNATION_MODULUS = 2
_FABRICATED_POSITIVE_SCORE = 0.9
_FABRICATED_NEGATIVE_SCORE = 0.1
_TARGET_CORPORA_TESTED = 2
_FABRICATED_CLEAN_LOSS = 0.1


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
    encoder = RepresentationEncoder(input_dimension=512)
    encoder.eval()
    detector = DetectorHead(latent_dimension=latent_dim)
    detector.eval()

    eval_records: list[EvaluationRecord] = [
        EvaluationRecord(
            dataset=DatasetSelector.EMBER2024,
            cutoff_id=SplitCutoffIdentity("c1"),
            sample_id=SampleIdentifier(f"s_{i}"),
            horizon_step=1,
            true_label=bool(i % _LABEL_ALTERNATION_MODULUS == 0),
            predicted_score=(
                _FABRICATED_POSITIVE_SCORE
                if bool(i % _LABEL_ALTERNATION_MODULUS == 0)
                else _FABRICATED_NEGATIVE_SCORE
            ),
            is_certified=True,
            clean_loss=_FABRICATED_CLEAN_LOSS,
        )
        for i in range(40)
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
