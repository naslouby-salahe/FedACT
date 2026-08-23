from __future__ import annotations

import random

import numpy as np

from fedact.runtime.determinism import SeedValue, apply_python_seed, create_numpy_generator


def test_numpy_generator_is_reproducible_from_the_same_seed() -> None:
    first = create_numpy_generator(SeedValue(2001))
    second = create_numpy_generator(SeedValue(2001))
    assert np.array_equal(first.random(8), second.random(8))


def test_different_seeds_produce_independent_streams() -> None:
    first = create_numpy_generator(SeedValue(2001))
    second = create_numpy_generator(SeedValue(2002))
    assert not np.array_equal(first.random(8), second.random(8))


def test_python_seed_reproduces_the_random_sequence() -> None:
    apply_python_seed(SeedValue(3001))
    first_sequence = [random.random() for _ in range(5)]
    apply_python_seed(SeedValue(3001))
    second_sequence = [random.random() for _ in range(5)]
    assert first_sequence == second_sequence
