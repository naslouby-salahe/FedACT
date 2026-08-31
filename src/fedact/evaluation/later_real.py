from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from fedact.domain.records import SampleCount

FloatArray = NDArray[np.float64]


@dataclass(frozen=True)
class LaterRealTransitionProxy:
    observed_transition: FloatArray
    sample_count: SampleCount


def build_later_real_proxy(
    embeddings_before: FloatArray,
    embeddings_after: FloatArray,
) -> LaterRealTransitionProxy:
    if embeddings_before.shape[0] == 0 or embeddings_after.shape[0] == 0:
        return LaterRealTransitionProxy(observed_transition=np.zeros(64), sample_count=0)
    delta = embeddings_after.mean(axis=0) - embeddings_before.mean(axis=0)
    return LaterRealTransitionProxy(
        observed_transition=delta,
        sample_count=min(embeddings_before.shape[0], embeddings_after.shape[0]),
    )
