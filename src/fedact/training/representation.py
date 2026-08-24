from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import torch
from torch.utils.data import DataLoader, TensorDataset

from fedact.config.models import FedActConfig
from fedact.domain.records import SampleIdentifier
from fedact.domain.types import (
    BinaryLabel,
    EpochIndex,
    LossValue,
    MetricRate,
    MonthIndex,
    RankDimension,
    SampleCount,
    SeedValue,
    ThresholdValue,
)
from fedact.models.representation import RepresentationEncoder


class TrainingContractError(ValueError):
    pass


@dataclass(frozen=True)
class PairedSeedIndex:
    representation_seed: SeedValue
    detector_training_seed: SeedValue


def paired_seed_index(config: FedActConfig, index: SeedValue) -> PairedSeedIndex:
    if index < 0 or index >= len(config.seeds.representation):
        raise TrainingContractError(f"Seed index {index} out of bounds")
    return PairedSeedIndex(
        representation_seed=config.seeds.representation[index],
        detector_training_seed=config.seeds.detector_training[index],
    )


def paired_seed_indices(
    representation_seeds: Sequence[SeedValue],
    detector_seeds: Sequence[SeedValue],
) -> tuple[PairedSeedIndex, ...]:
    if len(representation_seeds) != len(detector_seeds):
        raise ValueError("representation and detector seed streams must have equal length")
    return tuple(
        PairedSeedIndex(representation_seed=rep_seed, detector_training_seed=det_seed)
        for rep_seed, det_seed in zip(representation_seeds, detector_seeds, strict=True)
    )


@dataclass(frozen=True)
class TrainingObservation:
    sample_id: SampleIdentifier
    features: torch.Tensor | tuple[float, ...]
    month_index: MonthIndex
    label: BinaryLabel


@dataclass(frozen=True)
class RepresentationDataset:
    observations: tuple[TrainingObservation, ...]

    def feature_tensor(self) -> torch.Tensor:
        features = [
            torch.tensor(obs.features, dtype=torch.float32)
            if isinstance(obs.features, tuple)
            else obs.features
            for obs in self.observations
        ]
        return torch.stack(features)

    def label_tensor(self) -> torch.Tensor:
        return torch.tensor([1 if obs.label else 0 for obs in self.observations])

    def sample_ids(self) -> tuple[SampleIdentifier, ...]:
        return tuple(obs.sample_id for obs in self.observations)


@dataclass(frozen=True)
class SplitDatasets:
    training: RepresentationDataset
    validation: RepresentationDataset


@dataclass(frozen=True)
class EpochSelection:
    selected_epoch: EpochIndex
    selected_validation_loss: LossValue
    eligible_epochs: EpochIndex


def select_checkpoint_epoch(
    losses: Sequence[LossValue],
    tolerance: ThresholdValue = 1e-9,
    max_epochs: EpochIndex = 100,
) -> EpochSelection:
    if not losses:
        raise TrainingContractError("Loss history cannot be empty")
    best_loss = losses[0]
    best_epoch = 0
    for epoch, loss in enumerate(losses[: max_epochs + 1]):
        if loss < best_loss - tolerance:
            best_loss = loss
            best_epoch = epoch
    return EpochSelection(
        selected_epoch=best_epoch,
        selected_validation_loss=float(best_loss),
        eligible_epochs=len(losses),
    )


def select_best_epoch(validation_losses: Sequence[LossValue]) -> EpochSelection:
    return select_checkpoint_epoch(validation_losses)


def stratified_validation_split(
    population: Sequence[TrainingObservation],
    validation_fraction: MetricRate,
) -> tuple[tuple[TrainingObservation, ...], tuple[TrainingObservation, ...]]:
    strata: dict[tuple[bool, int], list[TrainingObservation]] = defaultdict(list)
    for obs in population:
        strata[(obs.label, obs.month_index)].append(obs)
    training: list[TrainingObservation] = []
    validation: list[TrainingObservation] = []
    for items in strata.values():
        if len(items) == 1:
            training.append(items[0])
            continue
        n_val = max(1, int(len(items) * validation_fraction))
        validation.extend(items[:n_val])
        training.extend(items[n_val:])
    return tuple(training), tuple(validation)


def partition_cutoff_dataset(
    observations: Sequence[TrainingObservation],
    cutoff_month: MonthIndex,
    validation_months_back: MonthIndex,
) -> SplitDatasets:
    training_cutoff = cutoff_month - validation_months_back
    train_obs: list[TrainingObservation] = []
    val_obs: list[TrainingObservation] = []
    for obs in observations:
        if obs.month_index <= training_cutoff:
            train_obs.append(obs)
        elif obs.month_index <= cutoff_month:
            val_obs.append(obs)
    return SplitDatasets(
        training=RepresentationDataset(observations=tuple(train_obs)),
        validation=RepresentationDataset(observations=tuple(val_obs)),
    )


def train_representation_encoder(
    training_dataset: RepresentationDataset,
    validation_dataset: RepresentationDataset,
    input_dimension: RankDimension,
    hidden_dimensions: Sequence[RankDimension],
    latent_dimension: RankDimension,
    epochs: EpochIndex,
    batch_size: SampleCount,
    learning_rate: ThresholdValue,
    weight_decay: ThresholdValue,
    random_seed: SeedValue,
) -> tuple[RepresentationEncoder, EpochSelection]:
    torch.manual_seed(random_seed)
    encoder = RepresentationEncoder(
        input_dimension=input_dimension,
        hidden_dimensions=hidden_dimensions,
        latent_dimension=latent_dimension,
    )
    optimizer = torch.optim.Adam(encoder.parameters(), lr=learning_rate, weight_decay=weight_decay)
    train_features = training_dataset.feature_tensor()
    train_labels = training_dataset.label_tensor().float()
    val_features = validation_dataset.feature_tensor()
    dataset = TensorDataset(train_features, train_labels)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_losses: list[float] = []
    saved_states: list[dict[str, torch.Tensor]] = []
    for _ in range(epochs):
        encoder.train()
        for batch_x, _ in loader:
            optimizer.zero_grad()
            latent = encoder(batch_x)
            loss = torch.mean(latent**2)
            loss.backward()
            optimizer.step()
        encoder.eval()
        with torch.no_grad():
            val_latent = encoder(val_features)
            val_loss = float(torch.mean(val_latent**2).item())
        val_losses.append(val_loss)
        saved_states.append({k: v.cpu().clone() for k, v in encoder.state_dict().items()})
    selection = select_best_epoch(tuple(val_losses))
    encoder.load_state_dict(saved_states[selection.selected_epoch])
    encoder.eval()
    return encoder, selection


def serialize_representation_encoder(
    encoder: RepresentationEncoder, destination_path: Path
) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(encoder.state_dict(), destination_path)


def load_representation_encoder(
    source_path: Path,
    input_dimension: RankDimension,
    hidden_dimensions: Sequence[RankDimension],
    latent_dimension: RankDimension,
) -> RepresentationEncoder:
    encoder = RepresentationEncoder(
        input_dimension=input_dimension,
        hidden_dimensions=hidden_dimensions,
        latent_dimension=latent_dimension,
    )
    state = torch.load(source_path, weights_only=True)
    encoder.load_state_dict(state)
    encoder.eval()
    return encoder


def apply_deterministic_torch_seed(seed: SeedValue) -> None:
    torch.manual_seed(seed)
