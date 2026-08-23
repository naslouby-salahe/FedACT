from __future__ import annotations

from collections.abc import Sequence

from fedact.domain.types import RankDimension
from fedact.scoring.encoding import EncodedSample


class ScoreValidationError(ValueError):
    pass


def validate_encoded_samples(
    samples: Sequence[EncodedSample],
    expected_dimension: RankDimension,
) -> None:
    for sample in samples:
        emb_shape = sample.embedding.shape
        dim = emb_shape[0] if len(emb_shape) > 0 else 0
        if dim != expected_dimension:
            raise ScoreValidationError(
                f"Expected embedding dimension {expected_dimension}, got {dim}"
            )
