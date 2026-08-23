from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch
from numpy.typing import NDArray

from fedact.domain.records import SampleIdentifier
from fedact.models.representation import RepresentationEncoder
from fedact.training.representation import TrainingObservation

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class EncodedSample:
    sample_id: SampleIdentifier
    embedding: FloatArray
    label: bool


def encode_observations(
    encoder: RepresentationEncoder,
    observations: tuple[TrainingObservation, ...],
) -> tuple[EncodedSample, ...]:
    encoder.eval()
    if not observations:
        return ()
    with torch.no_grad():
        features = torch.tensor([obs.features for obs in observations], dtype=torch.float32)
        embeddings = encoder(features).numpy()
    return tuple(
        EncodedSample(
            sample_id=obs.sample_id,
            embedding=embeddings[i].astype(np.float64),
            label=obs.label,
        )
        for i, obs in enumerate(observations)
    )
