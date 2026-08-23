from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, NewType

import torch
from pydantic import Field
from torch import nn

from fedact.config.models import FedActConfig, PositiveInt
from fedact.datasets.records import SampleIdentifier
from fedact.models.detector import DetectorHead
from fedact.models.representation import RepresentationEncoder

CheckpointHash = NewType("CheckpointHash", str)

ValidationFraction = Annotated[float, Field(ge=0.0, le=1.0)]
TieTolerance = Annotated[float, Field(gt=0.0)]
MeanLoss = Annotated[float, Field(ge=0.0)]


class TrainingContractError(ValueError):
    pass


SeedIndex = Annotated[int, Field(ge=0)]


def apply_deterministic_torch_seed(seed: SeedIndex) -> None:
    torch.use_deterministic_algorithms(True)
    torch.manual_seed(seed)


@dataclass(frozen=True)
class PairedSeedIndex:
    index: PositiveInt
    representation_seed: int
    detector_training_seed: int


def paired_seed_index(config: FedActConfig, index: SeedIndex) -> PairedSeedIndex:
    representations = config.seeds.representation
    detectors = config.seeds.detector_training
    if index >= len(representations) or index >= len(detectors):
        raise TrainingContractError(f"paired seed index {index} exceeds the configured seed arrays")
    return PairedSeedIndex(
        index=index,
        representation_seed=representations[index],
        detector_training_seed=detectors[index],
    )


@dataclass(frozen=True)
class TrainingObservation:
    sample_id: SampleIdentifier
    month_index: int
    label: bool
    features: tuple[float, ...]


def stratified_validation_split(
    observations: tuple[TrainingObservation, ...],
    validation_fraction: ValidationFraction,
) -> tuple[tuple[TrainingObservation, ...], tuple[TrainingObservation, ...]]:
    strata: dict[tuple[bool, int], list[TrainingObservation]] = {}
    for observation in observations:
        strata.setdefault((observation.label, observation.month_index), []).append(observation)
    training: list[TrainingObservation] = []
    validation: list[TrainingObservation] = []
    for key in sorted(strata):
        members = strata[key]
        if len(members) < 2:
            training.extend(members)
            continue
        validation_count = max(1, round(validation_fraction * len(members)))
        ordered = sorted(members, key=lambda item: item.sample_id)
        validation.extend(ordered[:validation_count])
        training.extend(ordered[validation_count:])
    return tuple(training), tuple(validation)


@dataclass(frozen=True)
class EpochSelection:
    selected_epoch: int
    selected_validation_loss: float
    eligible_epochs: int


def select_checkpoint_epoch(
    validation_losses: tuple[MeanLoss, ...],
    tie_tolerance: TieTolerance,
    early_stopping_patience_epochs: PositiveInt,
) -> EpochSelection:
    if not validation_losses:
        raise TrainingContractError("checkpoint selection requires at least one epoch")
    best_loss = min(validation_losses)
    best_epoch = validation_losses.index(best_loss)
    for epoch, loss in enumerate(validation_losses):
        if loss <= best_loss + tie_tolerance and epoch < best_epoch:
            best_loss = loss
            best_epoch = epoch
    last_improvement = best_epoch
    allowed_end = last_improvement + early_stopping_patience_epochs
    eligible = min(len(validation_losses), allowed_end + 1)
    return EpochSelection(
        selected_epoch=best_epoch,
        selected_validation_loss=validation_losses[best_epoch],
        eligible_epochs=eligible,
    )


def cosine_schedule_optimizer(
    model: nn.Module, config: FedActConfig
) -> tuple[torch.optim.Optimizer, torch.optim.lr_scheduler.LRScheduler]:
    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=config.training.initial_learning_rate,
        weight_decay=0.0,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer,
        T_max=config.training.maximum_epochs,
        eta_min=config.training.final_learning_rate,
    )
    return optimizer, scheduler


def train_base_detector(
    encoder: RepresentationEncoder,
    head: DetectorHead,
    training_population: tuple[TrainingObservation, ...],
    validation_population: tuple[TrainingObservation, ...],
    config: FedActConfig,
    seeds: PairedSeedIndex,
) -> EpochSelection:
    apply_deterministic_torch_seed(seeds.detector_training_seed)
    loss_fn = nn.BCEWithLogitsLoss()
    combined = nn.Sequential(encoder, head)
    optimizer, scheduler = cosine_schedule_optimizer(combined, config)

    def _run_epoch(population: tuple[TrainingObservation, ...]) -> MeanLoss:
        combined.train(False) if not population else None
        losses: list[float] = []
        batch_size = config.training.batch_size
        for start in range(0, len(population), batch_size):
            batch = population[start : start + batch_size]
            features = torch.tensor([item.features for item in batch], dtype=torch.float32)
            labels = torch.tensor([[float(item.label)] for item in batch], dtype=torch.float32)
            logits = combined(features)
            losses.append(float(loss_fn(logits, labels).item()))
        return sum(losses) / len(losses) if losses else 0.0

    history: list[float] = []
    patience = config.training.early_stopping_patience_epochs
    best_so_far = float("inf")
    epochs_since_improvement = 0
    for _ in range(config.training.maximum_epochs):
        combined.train(True)
        batch_size = config.training.batch_size
        permutation = list(range(len(training_population)))
        for start in range(0, len(permutation), batch_size):
            batch_indices = permutation[start : start + batch_size]
            batch = [training_population[i] for i in batch_indices]
            features = torch.tensor([item.features for item in batch], dtype=torch.float32)
            labels = torch.tensor([[float(item.label)] for item in batch], dtype=torch.float32)
            optimizer.zero_grad()
            loss = loss_fn(combined(features), labels)
            loss.backward()
            optimizer.step()
        scheduler.step()
        combined.train(False)
        validation_loss = _run_epoch(validation_population)
        history.append(validation_loss)
        if validation_loss < best_so_far - config.numerical.projection_tie_tolerance:
            best_so_far = validation_loss
            epochs_since_improvement = 0
        else:
            epochs_since_improvement += 1
            if epochs_since_improvement >= patience:
                break
    return select_checkpoint_epoch(
        tuple(history),
        config.numerical.projection_tie_tolerance,
        config.training.early_stopping_patience_epochs,
    )
