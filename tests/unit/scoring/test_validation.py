from __future__ import annotations

import numpy as np
import pytest

from fedact.domain.records import SampleIdentifier
from fedact.scoring.encoding import EncodedSample
from fedact.scoring.validation import ScoreValidationError, validate_encoded_samples


def test_validate_encoded_samples_checks_dimension() -> None:
    sample = EncodedSample(
        sample_id=SampleIdentifier("s1"),
        embedding=np.zeros(64),
        label=False,
    )
    validate_encoded_samples((sample,), expected_dimension=64)

    bad_sample = EncodedSample(
        sample_id=SampleIdentifier("s2"),
        embedding=np.zeros(32),
        label=False,
    )
    with pytest.raises(ScoreValidationError):
        validate_encoded_samples((bad_sample,), expected_dimension=64)
