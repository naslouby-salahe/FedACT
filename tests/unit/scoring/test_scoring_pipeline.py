from __future__ import annotations

from pathlib import Path

import pytest
import torch

from fedact.domain.types import SampleIdentifier
from fedact.learning.detector import DetectorHead
from fedact.learning.representation import RepresentationEncoder, TrainingObservation
from fedact.learning.scoring import (
    EncodedSample,
    ScoringContractError,
    compute_detector_scores,
    encode_dataset,
    encode_observations,
    load_scored_samples,
    materialize_embeddings,
    score_samples,
    serialize_scored_samples,
    validate_scored_samples,
)

INPUT_DIMENSION = 2
LATENT_DIMENSION = 3
ROWS = 4


def _encoder() -> RepresentationEncoder:
    return RepresentationEncoder(
        input_dimension=INPUT_DIMENSION,
        hidden_dimensions=(4,),
        latent_dimension=LATENT_DIMENSION,
    )


def _detector() -> DetectorHead:
    return DetectorHead(latent_dimension=LATENT_DIMENSION)


def _features(rows: int = ROWS) -> torch.Tensor:
    generator = torch.Generator().manual_seed(11)
    return torch.rand((rows, INPUT_DIMENSION), generator=generator, dtype=torch.float32)


def _sample_ids(rows: int = ROWS) -> tuple[SampleIdentifier, ...]:
    return tuple(SampleIdentifier(f"sample-{index}") for index in range(rows))


def _observation(index: int) -> TrainingObservation:
    return TrainingObservation(
        sample_id=SampleIdentifier(f"sample-{index}"),
        month_index=index % 3,
        label=index % 2 == 0,
        features=(1.0, 2.0),
    )


def test_encoded_sample_exposes_its_embedding_as_the_representation() -> None:
    embedding = torch.zeros(LATENT_DIMENSION)
    sample = EncodedSample(sample_id=SampleIdentifier("s"), embedding=embedding, label=True)
    assert sample.representation is embedding


def test_encoding_no_observations_yields_nothing() -> None:
    assert encode_observations(_encoder(), ()) == ()


def test_encoding_observations_preserves_identity_and_label() -> None:
    encoded = encode_observations(_encoder(), tuple(_observation(index) for index in range(ROWS)))
    assert len(encoded) == ROWS
    assert encoded[0].sample_id == "sample-0"
    assert encoded[0].label is True
    assert encoded[1].label is False


def test_encoding_no_sample_ids_yields_nothing() -> None:
    assert encode_dataset(_encoder(), (), _features(0), ()) == ()


def test_encoding_a_dataset_pairs_ids_with_labels() -> None:
    labels = [index % 2 == 0 for index in range(ROWS)]
    encoded = encode_dataset(_encoder(), _sample_ids(), _features(), labels)
    assert len(encoded) == ROWS
    assert [sample.label for sample in encoded] == labels


def test_materializing_no_observations_is_rejected() -> None:
    with pytest.raises(ScoringContractError, match="cannot be empty"):
        materialize_embeddings(_encoder(), ())


def test_materializing_embeddings_returns_one_row_per_observation() -> None:
    encoded = materialize_embeddings(_encoder(), tuple(_observation(i) for i in range(ROWS)))
    assert len(encoded) == ROWS


def test_scoring_no_encoded_samples_is_rejected() -> None:
    with pytest.raises(ScoringContractError, match="cannot be empty for scoring"):
        compute_detector_scores(_detector(), ())


def test_detector_scores_are_probabilities_of_the_logits() -> None:
    encoded = encode_observations(_encoder(), tuple(_observation(i) for i in range(ROWS)))
    scored = compute_detector_scores(_detector(), encoded)
    assert len(scored) == ROWS
    for sample in scored:
        assert 0.0 <= sample.probability <= 1.0
        assert sample.predicted_label == (sample.probability >= 0.5)


def test_scoring_without_samples_returns_nothing() -> None:
    assert score_samples(_encoder(), _detector(), (), _features(0)) == ()
    assert score_samples(_encoder(), _detector(), _sample_ids(), _features(0)) == ()


def test_scoring_produces_a_label_for_every_sample_id() -> None:
    scored = score_samples(_encoder(), _detector(), _sample_ids(), _features())
    assert [sample.sample_id for sample in scored] == [f"sample-{i}" for i in range(ROWS)]
    assert all(0.0 <= sample.probability <= 1.0 for sample in scored)


def test_scored_samples_round_trip_through_disk(tmp_path: Path) -> None:
    scored = score_samples(_encoder(), _detector(), _sample_ids(), _features())
    destination = tmp_path / "artifacts" / "scores.pt"
    serialize_scored_samples(scored, destination)
    assert destination.is_file()

    restored = load_scored_samples(destination)
    assert len(restored) == len(scored)
    for original, reloaded in zip(scored, restored, strict=True):
        assert reloaded.sample_id == original.sample_id
        assert reloaded.logit == pytest.approx(original.logit)
        assert reloaded.probability == pytest.approx(original.probability)
        assert reloaded.predicted_label == original.predicted_label


def test_serializing_no_samples_writes_an_empty_payload(tmp_path: Path) -> None:
    destination = tmp_path / "scores.pt"
    serialize_scored_samples((), destination)
    assert load_scored_samples(destination) == ()


def test_scored_sample_validation_passes_for_a_matching_population() -> None:
    scored = score_samples(_encoder(), _detector(), _sample_ids(), _features())
    report = validate_scored_samples([sample.sample_id for sample in scored], scored)
    assert report.identity_preserved is True
    assert report.all_probabilities_finite is True
    assert report.is_passing is True
    assert report.expected_sample_count == report.scored_sample_count


def test_scored_sample_validation_flags_a_missing_sample() -> None:
    scored = score_samples(_encoder(), _detector(), _sample_ids(), _features())
    report = validate_scored_samples([SampleIdentifier("absent")], scored)
    assert report.identity_preserved is False
    assert report.is_passing is False
    assert report.expected_sample_count == 1
    assert report.scored_sample_count == len(scored)
