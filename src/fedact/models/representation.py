from __future__ import annotations

import torch
from torch import Tensor, nn

EMBEDDING_DIMENSION = 64
DETECTOR_THRESHOLD = 1 / 2


class RepresentationEncoder(nn.Module):
    def __init__(self, input_dimension: int) -> None:
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dimension, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(0.10),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.10),
            nn.Linear(256, EMBEDDING_DIMENSION),
        )

    def forward(self, features: Tensor) -> Tensor:
        return self.network(features)


class DetectorHead(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.head = nn.Linear(EMBEDDING_DIMENSION, 1)

    def forward(self, embeddings: Tensor) -> Tensor:
        return self.head(embeddings)


def detector_probabilities(logits: Tensor) -> Tensor:
    return torch.sigmoid(logits)


def detector_predictions(probabilities: Tensor) -> Tensor:
    return (probabilities >= DETECTOR_THRESHOLD).to(dtype=probabilities.dtype)
