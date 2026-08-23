from __future__ import annotations

from dataclasses import dataclass

import torch

from fedact.datasets.records import SampleIdentifier
from fedact.models.detector import DetectorHead, detector_predictions, detector_probabilities
from fedact.models.representation import RepresentationEncoder
from fedact.training.representation import TrainingObservation


class ScoringContractError(ValueError):
    pass


@dataclass(frozen=True)
class EncodedSample:
    sample_id: SampleIdentifier
    embedding: tuple[float, ...]


@dataclass(frozen=True)
class ScoredSample:
    sample_id: SampleIdentifier
    logit: float
    probability: float
    predicted_label: bool


def materialize_embeddings(
    encoder: RepresentationEncoder,
    population: tuple[TrainingObservation, ...],
) -> tuple[EncodedSample, ...]:
    if not population:
        raise ScoringContractError("embedding materialization requires a non-empty population")
    encoder.eval()
    with torch.no_grad():
        features = torch.tensor([item.features for item in population], dtype=torch.float32)
        embeddings = encoder(features)
        rows = embeddings.tolist()
    return tuple(
        EncodedSample(sample_id=item.sample_id, embedding=tuple(float(value) for value in row))
        for item, row in zip(population, rows, strict=True)
    )


def compute_detector_scores(
    head: DetectorHead,
    encoded: tuple[EncodedSample, ...],
) -> tuple[ScoredSample, ...]:
    if not encoded:
        raise ScoringContractError("detector scoring requires at least one encoded sample")
    head.eval()
    with torch.no_grad():
        features = torch.tensor([sample.embedding for sample in encoded], dtype=torch.float32)
        logits = head(features).squeeze(dim=1)
        probabilities = detector_probabilities(logits)
        predictions = detector_predictions(probabilities)
    logit_values: list[float] = [float(value) for value in logits.detach().cpu().numpy().tolist()]
    probability_values: list[float] = [
        float(value) for value in probabilities.detach().cpu().numpy().tolist()
    ]
    prediction_values: list[bool] = [
        bool(int(value)) for value in predictions.detach().cpu().numpy().tolist()
    ]
    return tuple(
        ScoredSample(
            sample_id=sample.sample_id,
            logit=logit_value,
            probability=probability_value,
            predicted_label=prediction_value,
        )
        for sample, logit_value, probability_value, prediction_value in zip(
            encoded, logit_values, probability_values, prediction_values, strict=True
        )
    )


@dataclass(frozen=True)
class ScoringValidationReport:
    expected_sample_count: int
    scored_sample_count: int
    all_probabilities_finite: bool
    identity_preserved: bool

    @property
    def is_passing(self) -> bool:
        return (
            self.expected_sample_count == self.scored_sample_count
            and self.all_probabilities_finite
            and self.identity_preserved
        )


def validate_scoring_output(
    population: tuple[TrainingObservation, ...],
    scores: tuple[ScoredSample, ...],
) -> ScoringValidationReport:
    expected_ids = [item.sample_id for item in population]
    scored_ids = [score.sample_id for score in scores]
    finite = all(score.probability == score.probability for score in scores)
    return ScoringValidationReport(
        expected_sample_count=len(expected_ids),
        scored_sample_count=len(scored_ids),
        all_probabilities_finite=finite,
        identity_preserved=expected_ids == scored_ids,
    )
