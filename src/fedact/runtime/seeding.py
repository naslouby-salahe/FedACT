from __future__ import annotations

import random

import numpy as np

from fedact.domain.records import SeedValue


def apply_python_seed(seed: SeedValue) -> None:
    random.seed(seed)


def create_numpy_generator(seed: SeedValue) -> np.random.Generator:
    seed_sequence = np.random.SeedSequence(seed)
    return np.random.default_rng(seed_sequence)
