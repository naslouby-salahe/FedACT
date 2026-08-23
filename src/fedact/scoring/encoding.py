from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import torch

from fedact.domain.records import SampleIdentifier
from fedact.domain.types import BinaryLabel
from fedact.models.representation import RepresentationEncoder
from fedact.training.representation import TrainingObservation


@dataclass(frozen=True)
class EncodedSample:
    sample_id: SampleIdentifier
    embedding: np.ndarray | torch.Tensor
    label: BinaryLabel

    @property
    def representation(self) -> np.ndarray | torch.Tensor:
        return self.embedding


def encode_observations(
    encoder: RepresentationEncoder,
    observations: Sequence[TrainingObservation],
) -> tuple[EncodedSample, ...]:
    if not observations:
        return ()
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


def encode_dataset(
    encoder: RepresentationEncoder,
    sample_ids: Sequence[SampleIdentifier],
    features: torch.Tensor,
    labels: Sequence[BinaryLabel],
) -> tuple[EncodedSample, ...]:
    if not sample_ids:
        return ()
    encoder.eval()
    with torch.no_grad():
        encoded = encoder(features)
    return tuple(
        EncodedSample(
            sample_id=s_id,
            embedding=encoded[idx],
            label=lbl,
        )
        for idx, (s_id, lbl) in enumerate(zip(sample_ids, labels, strict=True))
    )
