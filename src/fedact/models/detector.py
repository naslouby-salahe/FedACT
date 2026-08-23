from __future__ import annotations

import torch
from torch import Tensor, nn

from fedact.models.representation import DETECTOR_THRESHOLD, EMBEDDING_DIMENSION


class DetectorHead(nn.Module):
    def __init__(self, latent_dimension: int = EMBEDDING_DIMENSION) -> None:
        super().__init__()
        self.head = nn.Linear(latent_dimension, 1)

    def forward(self, embeddings: Tensor) -> Tensor:
        return self.head(embeddings)


def detector_probabilities(logits: Tensor) -> Tensor:
    return torch.sigmoid(logits)


def detector_predictions(probabilities: Tensor) -> Tensor:
    return (probabilities >= DETECTOR_THRESHOLD).to(dtype=probabilities.dtype)
