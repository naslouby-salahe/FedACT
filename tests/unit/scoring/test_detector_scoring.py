from __future__ import annotations

import pytest
import torch

from fedact.datasets.records import SampleIdentifier
from fedact.models.detector import DetectorHead, detector_predictions, detector_probabilities
from fedact.models.representation import EMBEDDING_DIMENSION, RepresentationEncoder
from fedact.scoring.detector import (
    ScoringContractError,
    compute_detector_scores,
    materialize_embeddings,
    validate_scoring_output,
)
from fedact.training.representation import TrainingObservation


def observation(sid: str) -> TrainingObservation:
    return TrainingObservation(
        sample_id=SampleIdentifier(sid), month_index=1, label=True, features=(0.5, -0.5)
    )


def small_encoder() -> RepresentationEncoder:
    encoder = RepresentationEncoder(input_dimension=2)
    with torch.no_grad():
        for parameter in encoder.parameters():
            parameter.fill_(0.01)
    return encoder


def test_materialized_embeddings_have_the_locked_dimension() -> None:
    population = (observation("a"), observation("b"))
    encoded = materialize_embeddings(small_encoder(), population)
    assert all(len(sample.embedding) == EMBEDDING_DIMENSION for sample in encoded)


def test_empty_population_is_rejected_for_embedding_and_scoring() -> None:
    encoder = small_encoder()
    head = DetectorHead()
    with pytest.raises(ScoringContractError):
        materialize_embeddings(encoder, ())
    encoded = materialize_embeddings(encoder, (observation("a"),))
    assert len(encoded) == 1
    with pytest.raises(ScoringContractError):
        compute_detector_scores(head, ())


def test_scoring_preserves_sample_identity_and_probability_semantics() -> None:
    population = (observation("a"), observation("b"), observation("c"))
    encoded = materialize_embeddings(small_encoder(), population)
    scores = compute_detector_scores(DetectorHead(), encoded)
    assert [score.sample_id for score in scores] == [item.sample_id for item in population]
    probabilities = detector_probabilities(torch.tensor([score.logit for score in scores]))
    assert torch.all((probabilities >= 0.0) & (probabilities <= 1.0))
    predictions = detector_predictions(probabilities)
    assert all(
        score.predicted_label == bool(int(prediction.item()))
        for score, prediction in zip(scores, predictions, strict=True)
    )


def test_validation_report_detects_identity_mismatch() -> None:
    population = (observation("a"), observation("b"))
    encoded = materialize_embeddings(small_encoder(), population)
    scores = compute_detector_scores(DetectorHead(), encoded)
    report = validate_scoring_output(population, scores)
    assert report.is_passing
    reordered = tuple(reversed(scores))
    broken = validate_scoring_output(population, reordered)
    assert not broken.identity_preserved


def test_deterministic_replay_of_scoring_pipeline() -> None:
    torch.manual_seed(11)
    population = tuple(observation(f"s{i}") for i in range(4))
    encoder = small_encoder()
    head = DetectorHead()
    first = compute_detector_scores(head, materialize_embeddings(encoder, population))
    second = compute_detector_scores(head, materialize_embeddings(encoder, population))
    assert [score.logit for score in first] == [score.logit for score in second]
