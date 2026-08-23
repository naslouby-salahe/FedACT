from __future__ import annotations

import random
from typing import NewType

import numpy as np

SeedValue = NewType("SeedValue", int)


def apply_python_seed(seed: SeedValue) -> None:
    random.seed(seed)


def create_numpy_generator(seed: SeedValue) -> np.random.Generator:
    return np.random.default_rng(seed)
