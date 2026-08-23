from __future__ import annotations

from fedact.domain.records import SampleIdentifier
from fedact.models.representation import RepresentationEncoder
from fedact.scoring.encoding import encode_observations
from fedact.training.representation import TrainingObservation


def test_encode_observations_produces_64d_embeddings() -> None:
    encoder = RepresentationEncoder(input_dimension=512)
    obs = (
        TrainingObservation(
            sample_id=SampleIdentifier("s1"),
            month_index=0,
            features=(0.1,) * 512,
            label=True,
        ),
    )
    encoded = encode_observations(encoder, obs)
    assert len(encoded) == 1
    assert encoded[0].embedding.shape == (64,)
