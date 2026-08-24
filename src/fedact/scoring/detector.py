from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

from fedact.domain.records import SampleIdentifier
from fedact.domain.types import (
    BinaryLabel,
    LogitValue,
    ProbabilityValue,
    SampleCount,
    ValidationFlag,
)
from fedact.models.detector import DetectorHead
from fedact.models.representation import RepresentationEncoder
from fedact.scoring.encoding import EncodedSample
from fedact.training.representation import TrainingObservation


class ScoringContractError(ValueError):
    pass


@dataclass(frozen=True)
class ScoredSample:
    sample_id: SampleIdentifier
    logit: LogitValue
    probability: ProbabilityValue
    predicted_label: BinaryLabel


def materialize_embeddings(
    encoder: RepresentationEncoder,
    observations: Sequence[TrainingObservation],
) -> tuple[EncodedSample, ...]:
    if not observations:
        raise ScoringContractError("Observations population cannot be empty")
    encoder.eval()
    features = torch.stack(
        [
            torch.tensor(obs.features, dtype=torch.float32)
            if isinstance(obs.features, tuple)
            else obs.features
            for obs in observations
        ]
    )
    with torch.no_grad():
        encoded = encoder(features)
    return tuple(
        EncodedSample(
            sample_id=obs.sample_id,
            embedding=np.array(encoded[idx].cpu().numpy()),
            label=obs.label,
        )
        for idx, obs in enumerate(observations)
    )


def compute_detector_scores(
    detector: DetectorHead,
    samples: Sequence[EncodedSample],
) -> tuple[ScoredSample, ...]:
    if not samples:
        raise ScoringContractError("Samples cannot be empty for scoring")
    detector.eval()
    embeddings = torch.stack(
        [
            torch.tensor(s.embedding, dtype=torch.float32)
            if isinstance(s.embedding, (np.ndarray, tuple))
            else s.embedding
            for s in samples
        ]
    )
    with torch.no_grad():
        logits = detector(embeddings)
        probabilities = torch.sigmoid(logits)
    scored: list[ScoredSample] = []
    for idx, sample in enumerate(samples):
        logit_val = float(logits[idx].item())
        prob_val = float(probabilities[idx].item())
        scored.append(
            ScoredSample(
                sample_id=sample.sample_id,
                logit=logit_val,
                probability=prob_val,
                predicted_label=bool(prob_val >= 0.5),
            )
        )
    return tuple(scored)


@dataclass(frozen=True)
class ScoringValidationReport:
    expected_sample_count: SampleCount
    scored_sample_count: SampleCount
    all_probabilities_finite: ValidationFlag
    identity_preserved: ValidationFlag

    @property
    def is_passing(self) -> bool:
        return self.all_probabilities_finite and self.identity_preserved


def validate_scoring_output(
    expected_population: Sequence[TrainingObservation | SampleIdentifier],
    scores: Sequence[ScoredSample],
) -> ScoringValidationReport:
    expected_ids = tuple(
        item.sample_id if isinstance(item, TrainingObservation) else item
        for item in expected_population
    )
    actual_ids = tuple(s.sample_id for s in scores)
    all_finite = all(0.0 <= s.probability <= 1.0 for s in scores)
    identity_ok = expected_ids == actual_ids
    return ScoringValidationReport(
        expected_sample_count=len(expected_population),
        scored_sample_count=len(scores),
        all_probabilities_finite=all_finite,
        identity_preserved=identity_ok,
    )


def validate_scored_samples(
    expected_sample_ids: Sequence[SampleIdentifier],
    scored_samples: Sequence[ScoredSample],
) -> ScoringValidationReport:
    return validate_scoring_output(expected_sample_ids, scored_samples)


def score_samples(
    encoder: RepresentationEncoder,
    detector: DetectorHead,
    sample_ids: Sequence[SampleIdentifier],
    features: torch.Tensor,
) -> tuple[ScoredSample, ...]:
    if not sample_ids or features.shape[0] == 0:
        return ()
    encoder.eval()
    detector.eval()
    with torch.no_grad():
        encoded = encoder(features)
        logits = detector(encoded)
        probabilities = torch.sigmoid(logits)
    scored: list[ScoredSample] = []
    for idx, sample_id in enumerate(sample_ids):
        logit_val = float(logits[idx].item())
        prob_val = float(probabilities[idx].item())
        scored.append(
            ScoredSample(
                sample_id=sample_id,
                logit=logit_val,
                probability=prob_val,
                predicted_label=bool(prob_val >= 0.5),
            )
        )
    return tuple(scored)


def serialize_scored_samples(
    scored_samples: Sequence[ScoredSample], destination_path: Path
) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "sample_ids": [s.sample_id for s in scored_samples],
        "logits": [s.logit for s in scored_samples],
        "probabilities": [s.probability for s in scored_samples],
        "predicted_labels": [s.predicted_label for s in scored_samples],
    }
    torch.save(payload, destination_path)


def load_scored_samples(source_path: Path) -> tuple[ScoredSample, ...]:
    payload = torch.load(source_path, weights_only=True)
    scored: list[ScoredSample] = []
    for s_id, logit, prob, label in zip(
        payload["sample_ids"],
        payload["logits"],
        payload["probabilities"],
        payload["predicted_labels"],
        strict=True,
    ):
        scored.append(
            ScoredSample(
                sample_id=SampleIdentifier(s_id),
                logit=float(logit),
                probability=float(prob),
                predicted_label=bool(label),
            )
        )
    return tuple(scored)
