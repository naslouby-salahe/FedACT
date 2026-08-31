from __future__ import annotations

from pathlib import Path

import pytest

from fedact.config.loading import LoadedConfiguration, load_production_configuration
from fedact.config.models import FedActConfig
from fedact.domain.records import SampleIdentifier
from fedact.training.representation import (
    PairedSeedIndex,
    TrainingContractError,
    TrainingObservation,
    paired_seed_indices,
    select_checkpoint_epoch,
    stratified_validation_split,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def config() -> FedActConfig:
    loaded: LoadedConfiguration = load_production_configuration(
        REPOSITORY_ROOT / "configs" / "fedact.yaml"
    )
    return loaded.values


def observation(sid: str, month: int, label: bool) -> TrainingObservation:
    return TrainingObservation(
        sample_id=SampleIdentifier(sid),
        month_index=month,
        label=label,
        features=(1.0, 2.0),
    )


def test_paired_seed_indices_never_substitute_streams(config: FedActConfig) -> None:
    seeds = paired_seed_indices(
        tuple(config.seeds.representation[:2]),
        tuple(config.seeds.detector_training[:2]),
    )
    assert seeds[0] == PairedSeedIndex(
        representation_seed=config.seeds.representation[0],
        detector_training_seed=config.seeds.detector_training[0],
    )
    assert seeds[1] == PairedSeedIndex(
        representation_seed=config.seeds.representation[1],
        detector_training_seed=config.seeds.detector_training[1],
    )


def test_validation_split_is_stratified_by_label_and_month(config: FedActConfig) -> None:
    population = tuple(
        [observation(f"m{i}", i % 3, True) for i in range(30)]
        + [observation(f"b{i}", i % 3, False) for i in range(30)]
    )
    training, validation = stratified_validation_split(
        population, config.training.validation_fraction
    )
    assert bool(training)
    assert bool(validation)
    validation_strata = {(item.label, item.month_index) for item in validation}
    expected_strata = {(label, month) for label in (True, False) for month in range(3)}
    assert validation_strata == expected_strata


def test_singleton_stratum_stays_in_training_and_never_duplicates(config: FedActConfig) -> None:
    population = (
        observation("single", 99, True),
        observation("a", 1, True),
        observation("b", 1, False),
        observation("c", 1, True),
        observation("d", 1, False),
    )
    training, validation = stratified_validation_split(population, 0.5)
    singleton_in_validation = [item for item in validation if item.month_index == 99]
    assert not singleton_in_validation
    assert sum(1 for item in training if item.month_index == 99) == 1


def test_checkpoint_tie_goes_to_the_earlier_epoch() -> None:
    selection = select_checkpoint_epoch((1.0, 0.6, 0.6), 1e-9, 5)
    assert selection.selected_epoch == 1
    tied = select_checkpoint_epoch((0.5, 0.5 + 1e-12), 1e-9, 5)
    assert tied.selected_epoch == 0


def test_epoch_selection_requires_history() -> None:
    with pytest.raises(TrainingContractError):
        select_checkpoint_epoch((), 1e-9, 5)


def test_selected_epoch_comes_from_the_same_history_for_encoder_and_head(
    config: FedActConfig,
) -> None:
    losses = (2.0, 1.0, 0.8, 0.9, 0.85, 0.7)
    selection = select_checkpoint_epoch(losses, config.numerical.projection_tie_tolerance, 5)
    assert losses[selection.selected_epoch] == min(losses)
