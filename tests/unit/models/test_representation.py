from __future__ import annotations

import torch

from fedact.models.detector import (
    DetectorHead,
    detector_predictions,
    detector_probabilities,
)
from fedact.models.representation import (
    DETECTOR_THRESHOLD,
    EMBEDDING_DIMENSION,
    RepresentationEncoder,
)


def test_encoder_outputs_exactly_64_linear_dimensions() -> None:
    encoder = RepresentationEncoder(input_dimension=20)
    features = torch.randn(8, 20)
    embedding = encoder(features)
    assert embedding.shape == (8, EMBEDDING_DIMENSION)


def test_detector_head_is_a_single_linear_layer_over_the_embedding() -> None:
    head = DetectorHead()
    parameters = [module for module in head.modules() if isinstance(module, torch.nn.Linear)]
    assert len(parameters) == 1
    assert parameters[0].in_features == EMBEDDING_DIMENSION
    assert parameters[0].out_features == 1


def test_training_operates_on_logits_and_sigmoid_only_for_inference() -> None:
    logits = torch.tensor([-4.0, 0.0, 3.0])
    probabilities = detector_probabilities(logits)
    assert probabilities[0] < DETECTOR_THRESHOLD
    assert probabilities[1] == DETECTOR_THRESHOLD
    assert probabilities[2] > DETECTOR_THRESHOLD


def test_fixed_half_threshold_is_not_tuned() -> None:
    assert DETECTOR_THRESHOLD == 0.5
    scores = torch.tensor([0.49, 0.5, 0.51])
    predictions = detector_predictions(scores)
    assert predictions.tolist() == [0.0, 1.0, 1.0]


def test_encoder_dropout_respects_the_locked_rate() -> None:
    encoder = RepresentationEncoder(input_dimension=10)
    dropout_modules = [
        module for module in encoder.modules() if isinstance(module, torch.nn.Dropout)
    ]
    assert len(dropout_modules) == 2
    assert all(module.p == 0.10 for module in dropout_modules)


def test_batchnorm_and_relu_follow_the_locked_architecture_order() -> None:
    encoder = RepresentationEncoder(input_dimension=6)
    linear_dims = [
        module.out_features for module in encoder.modules() if isinstance(module, torch.nn.Linear)
    ]
    assert linear_dims == [512, 256, EMBEDDING_DIMENSION]
