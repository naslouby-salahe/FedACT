from __future__ import annotations

from pathlib import Path

import torch

from fedact.domain.types import SampleIdentifier
from fedact.learning.detector import (
    DetectorHead,
    detector_predictions,
    detector_probabilities,
    load_trained_detector,
    serialize_trained_detector,
    train_base_detector,
)
from fedact.learning.representation import (
    DETECTOR_THRESHOLD,
    EMBEDDING_DIMENSION,
    RepresentationDataset,
    RepresentationEncoder,
    TrainingObservation,
    load_representation_encoder,
    partition_cutoff_dataset,
    serialize_representation_encoder,
    train_representation_encoder,
)

INPUT_DIMENSION = 2
HIDDEN_DIMENSIONS = (4,)
LATENT_DIMENSION = 3
DETECTOR_EPOCHS = 3
REPRESENTATION_EPOCHS = 2
BATCH_SIZE = 8
LEARNING_RATE = 0.01
WEIGHT_DECAY = 0.0
TIE_TOLERANCE = 1.0e-9


def _features(rows: int) -> torch.Tensor:
    generator = torch.Generator().manual_seed(7)
    return torch.rand((rows, INPUT_DIMENSION), generator=generator, dtype=torch.float32)


def _labels(rows: int) -> torch.Tensor:
    return torch.tensor([[index % 2 == 0] for index in range(rows)], dtype=torch.float32)


def _encoder() -> RepresentationEncoder:
    return RepresentationEncoder(
        input_dimension=INPUT_DIMENSION,
        hidden_dimensions=HIDDEN_DIMENSIONS,
        latent_dimension=LATENT_DIMENSION,
    )


def _observation(sample_id: str, month_index: int, label: bool) -> TrainingObservation:
    return TrainingObservation(
        sample_id=SampleIdentifier(sample_id),
        month_index=month_index,
        label=label,
        features=(1.0, 2.0),
    )


def test_detector_head_projects_embeddings_to_a_single_logit() -> None:
    head = DetectorHead(latent_dimension=LATENT_DIMENSION)
    logits = head(torch.zeros((5, LATENT_DIMENSION), dtype=torch.float32))
    assert logits.shape == (5, 1)


def test_probabilities_and_predictions_share_the_detector_threshold() -> None:
    logits = torch.tensor([[0.0], [4.0], [-4.0]], dtype=torch.float32)
    probabilities = detector_probabilities(logits)
    assert probabilities.min() >= 0.0
    assert probabilities.max() <= 1.0
    predictions = detector_predictions(probabilities)
    assert predictions[0].item() == (DETECTOR_THRESHOLD <= 0.5)
    assert predictions[1].item() == 1.0
    assert predictions[2].item() == 0.0


def test_base_detector_training_is_deterministic_for_a_fixed_seed() -> None:
    train_features = _features(16)
    train_labels = _labels(16)
    val_features = _features(8)
    val_labels = _labels(8)

    shared_encoder = _encoder()
    first = train_base_detector(
        shared_encoder,
        train_features,
        train_labels,
        val_features,
        val_labels,
        DETECTOR_EPOCHS,
        BATCH_SIZE,
        LEARNING_RATE,
        WEIGHT_DECAY,
        representation_seed=1,
        detector_seed=2,
        tie_tolerance=TIE_TOLERANCE,
    )
    second = train_base_detector(
        shared_encoder,
        train_features,
        train_labels,
        val_features,
        val_labels,
        DETECTOR_EPOCHS,
        BATCH_SIZE,
        LEARNING_RATE,
        WEIGHT_DECAY,
        representation_seed=1,
        detector_seed=2,
        tie_tolerance=TIE_TOLERANCE,
    )
    assert first.detector_seed == 2
    assert first.representation_seed == 1
    assert first.selection.selected_epoch == second.selection.selected_epoch
    for name, parameter in first.detector.state_dict().items():
        assert torch.equal(parameter, second.detector.state_dict()[name])


def test_base_detector_selection_stays_within_the_epoch_budget() -> None:
    run = train_base_detector(
        _encoder(),
        _features(16),
        _labels(16),
        _features(8),
        _labels(8),
        DETECTOR_EPOCHS,
        BATCH_SIZE,
        LEARNING_RATE,
        WEIGHT_DECAY,
        representation_seed=3,
        detector_seed=4,
        tie_tolerance=TIE_TOLERANCE,
    )
    assert 0 <= run.selection.selected_epoch < DETECTOR_EPOCHS


def test_trained_detector_round_trips_through_disk(tmp_path: Path) -> None:
    run = train_base_detector(
        _encoder(),
        _features(16),
        _labels(16),
        _features(8),
        _labels(8),
        DETECTOR_EPOCHS,
        BATCH_SIZE,
        LEARNING_RATE,
        WEIGHT_DECAY,
        representation_seed=5,
        detector_seed=6,
        tie_tolerance=TIE_TOLERANCE,
    )
    destination = tmp_path / "artifacts" / "detector.pt"
    serialize_trained_detector(run.detector, destination)
    assert destination.is_file()

    restored = load_trained_detector(destination, LATENT_DIMENSION)
    for name, parameter in run.detector.state_dict().items():
        assert torch.equal(parameter, restored.state_dict()[name])


def test_representation_encoder_has_the_configured_latent_dimension() -> None:
    encoder = _encoder()
    embedded = encoder(_features(4))
    assert embedded.shape == (4, LATENT_DIMENSION)
    default_encoder = RepresentationEncoder(input_dimension=INPUT_DIMENSION)
    assert default_encoder(_features(4)).shape == (4, EMBEDDING_DIMENSION)


def test_training_and_validation_regions_split_on_the_cutoff() -> None:
    observations = tuple(
        _observation(f"sample-{month}", month, month % 2 == 0) for month in range(6)
    )
    split = partition_cutoff_dataset(observations, cutoff_month=4, validation_months_back=2)
    assert [obs.month_index for obs in split.training.observations] == [0, 1, 2]
    assert [obs.month_index for obs in split.validation.observations] == [3, 4]


def test_representation_training_returns_an_encoder_and_an_epoch_selection() -> None:
    observations = tuple(
        _observation(f"sample-{index}", month_index=index % 3, label=index % 2 == 0)
        for index in range(24)
    )
    dataset = RepresentationDataset(observations=observations)
    encoder, selection = train_representation_encoder(
        dataset,
        dataset,
        INPUT_DIMENSION,
        HIDDEN_DIMENSIONS,
        LATENT_DIMENSION,
        REPRESENTATION_EPOCHS,
        BATCH_SIZE,
        LEARNING_RATE,
        WEIGHT_DECAY,
        random_seed=11,
        tie_tolerance=TIE_TOLERANCE,
    )
    assert 0 <= selection.selected_epoch < REPRESENTATION_EPOCHS
    assert encoder(_features(4)).shape == (4, LATENT_DIMENSION)


def test_representation_encoder_round_trips_through_disk(tmp_path: Path) -> None:
    encoder = RepresentationEncoder(
        input_dimension=INPUT_DIMENSION,
        hidden_dimensions=HIDDEN_DIMENSIONS,
        latent_dimension=LATENT_DIMENSION,
    )
    destination = tmp_path / "artifacts" / "encoder.pt"
    serialize_representation_encoder(encoder, destination)
    assert destination.is_file()

    restored = load_representation_encoder(
        destination, INPUT_DIMENSION, HIDDEN_DIMENSIONS, LATENT_DIMENSION
    )
    assert not restored.training
    for name, parameter in encoder.state_dict().items():
        assert torch.equal(parameter, restored.state_dict()[name])
    assert restored(_features(4)).shape == (4, LATENT_DIMENSION)
