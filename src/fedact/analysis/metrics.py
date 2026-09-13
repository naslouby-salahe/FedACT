from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import cast

import numpy as np
import sklearn.metrics as sklearn_metrics
from numpy.typing import NDArray

from fedact.domain.types import (
    BinaryLabel,
    CatchUpStep,
    CertificationFlag,
    DatasetSelector,
    HorizonStep,
    LossValue,
    MetricRate,
    ProbabilityValue,
    SampleCount,
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
    is_certified: CertificationFlag
    clean_loss: LossValue


@dataclass(frozen=True)
class EvaluationMetrics:
    false_negative_rate: MetricRate
    certification_rate: MetricRate
    clean_fnr: MetricRate
    cumulative_exposure: MetricRate
    true_positive_rate: MetricRate
    false_positive_rate: MetricRate
    abstention_rate: MetricRate
    pr_auc: MetricRate | None = None
    roc_auc: MetricRate | None = None


def compute_evaluation_metrics(records: tuple[EvaluationRecord, ...]) -> EvaluationMetrics:
    if not records:
        return EvaluationMetrics(
            false_negative_rate=0.0,
            certification_rate=0.0,
            clean_fnr=0.0,
            cumulative_exposure=0.0,
            true_positive_rate=0.0,
            false_positive_rate=0.0,
            abstention_rate=0.0,
        )

    malicious = [r for r in records if r.true_label]
    benign = [r for r in records if not r.true_label]

    fnr = (
        sum(1 for r in malicious if r.predicted_score < 0.5) / len(malicious) if malicious else 0.0
    )
    clean_fnr = sum(1 for r in benign if r.predicted_score >= 0.5) / len(benign) if benign else 0.0
    cert_rate = sum(1 for r in records if r.is_certified) / len(records)
    exposure = float(sum(r.clean_loss for r in malicious))

    pr_auc: MetricRate | None = None
    roc_auc: MetricRate | None = None
    if malicious and benign:
        labels = np.fromiter((1.0 if r.true_label else 0.0 for r in records), dtype=np.float64)
        scores = np.fromiter((r.predicted_score for r in records), dtype=np.float64)
        pr_auc = float(cast(float, sklearn_metrics.average_precision_score(labels, scores)))
        roc_auc = float(cast(float, sklearn_metrics.roc_auc_score(labels, scores)))

    return EvaluationMetrics(
        false_negative_rate=fnr,
        certification_rate=cert_rate,
        clean_fnr=clean_fnr,
        cumulative_exposure=exposure,
        true_positive_rate=1.0 - fnr,
        false_positive_rate=clean_fnr,
        abstention_rate=1.0 - cert_rate,
        pr_auc=pr_auc,
        roc_auc=roc_auc,
    )


FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class LaterRealTransitionProxy:
    observed_transition: FloatArray
    sample_count: SampleCount


def build_later_real_proxy(
    embeddings_before: FloatArray,
    embeddings_after: FloatArray,
) -> LaterRealTransitionProxy:
    if embeddings_before.shape[0] == 0 or embeddings_after.shape[0] == 0:
        return LaterRealTransitionProxy(observed_transition=np.zeros(64), sample_count=0)
    delta = embeddings_after.mean(axis=0) - embeddings_before.mean(axis=0)
    return LaterRealTransitionProxy(
        observed_transition=delta,
        sample_count=min(embeddings_before.shape[0], embeddings_after.shape[0]),
    )


CumulativeLoss = LossValue
LossThreshold = LossValue


def compute_cumulative_exposure(losses: Sequence[LossValue]) -> CumulativeLoss:
    return float(sum(losses))


def compute_time_to_catch_up(
    baseline_losses: Sequence[LossValue],
    hardened_losses: Sequence[LossValue],
    threshold: LossThreshold,
) -> CatchUpStep | None:
    for t, (b, h) in enumerate(zip(baseline_losses, hardened_losses, strict=True)):
        if abs(h - b) <= threshold:
            return t
    return None


class MetricValidationError(ValueError):
    pass


def validate_evaluation_metrics(metrics: EvaluationMetrics) -> None:
    if not (0.0 <= metrics.false_negative_rate <= 1.0):
        raise MetricValidationError("false negative rate out of bounds [0, 1]")
    if not (0.0 <= metrics.certification_rate <= 1.0):
        raise MetricValidationError("certification rate out of bounds [0, 1]")
    if not (0.0 <= metrics.true_positive_rate <= 1.0):
        raise MetricValidationError("true positive rate out of bounds [0, 1]")
    if not (0.0 <= metrics.false_positive_rate <= 1.0):
        raise MetricValidationError("false positive rate out of bounds [0, 1]")
    if not (0.0 <= metrics.abstention_rate <= 1.0):
        raise MetricValidationError("abstention rate out of bounds [0, 1]")
    if metrics.pr_auc is not None and not (0.0 <= metrics.pr_auc <= 1.0):
        raise MetricValidationError("PR-AUC out of bounds [0, 1]")
    if metrics.roc_auc is not None and not (0.0 <= metrics.roc_auc <= 1.0):
        raise MetricValidationError("ROC-AUC out of bounds [0, 1]")
