from __future__ import annotations

from typing import Annotated

from pydantic import Field

from fedact.scoring.encoding import EncodedSample

TargetDimension = Annotated[int, Field(ge=1)]


class ScoreValidationError(ValueError):
    pass


def validate_encoded_samples(
    samples: tuple[EncodedSample, ...], expected_dimension: TargetDimension
) -> None:
    for s in samples:
        if s.embedding.shape != (expected_dimension,):
            raise ScoreValidationError(f"embedding dimension mismatch: {s.embedding.shape}")
