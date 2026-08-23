from __future__ import annotations

from collections.abc import Sequence

from torch import Tensor, nn

EMBEDDING_DIMENSION = 64
DETECTOR_THRESHOLD = 1 / 2


class RepresentationEncoder(nn.Module):
    def __init__(
        self,
        input_dimension: int,
        hidden_dimensions: Sequence[int] = (512, 256),
        latent_dimension: int = EMBEDDING_DIMENSION,
    ) -> None:
        super().__init__()
        layers: list[nn.Module] = []
        prev_dim = input_dimension
        for h_dim in hidden_dimensions:
            layers.extend(
                [
                    nn.Linear(prev_dim, h_dim),
                    nn.BatchNorm1d(h_dim),
                    nn.ReLU(),
                    nn.Dropout(0.10),
                ]
            )
            prev_dim = h_dim
        layers.append(nn.Linear(prev_dim, latent_dimension))
        self.network = nn.Sequential(*layers)

    def forward(self, features: Tensor) -> Tensor:
        return self.network(features)
