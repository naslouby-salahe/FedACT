from __future__ import annotations

from dataclasses import dataclass

from fedact.domain.records import MetricRate
from fedact.evaluation.records import EvaluationRecord


@dataclass(frozen=True)
class EvaluationMetrics:
    false_negative_rate: MetricRate
    certification_rate: MetricRate
    clean_fnr: MetricRate
    cumulative_exposure: MetricRate


def compute_evaluation_metrics(records: tuple[EvaluationRecord, ...]) -> EvaluationMetrics:
    if not records:
        return EvaluationMetrics(
            false_negative_rate=0.0, certification_rate=0.0, clean_fnr=0.0, cumulative_exposure=0.0
        )

    malicious = [r for r in records if r.true_label]
    benign = [r for r in records if not r.true_label]

    fnr = (
        sum(1 for r in malicious if r.predicted_score < 0.5) / len(malicious) if malicious else 0.0
    )
    clean_fnr = sum(1 for r in benign if r.predicted_score >= 0.5) / len(benign) if benign else 0.0
    cert_rate = sum(1 for r in records if r.is_certified) / len(records)
    exposure = float(sum(r.clean_loss for r in malicious))

    return EvaluationMetrics(
        false_negative_rate=fnr,
        certification_rate=cert_rate,
        clean_fnr=clean_fnr,
        cumulative_exposure=exposure,
    )
