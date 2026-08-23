from __future__ import annotations

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
