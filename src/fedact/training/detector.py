from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn

from fedact.config.models import FedActConfig
from fedact.models.detector import DetectorHead
from fedact.models.representation import RepresentationEncoder
from fedact.training.representation import (
    EpochSelection,
    PairedSeedIndex,
    TrainingObservation,
    apply_deterministic_torch_seed,
    select_checkpoint_epoch,
)


class DetectorTrainingError(ValueError):
    pass


@dataclass(frozen=True)
class BaseDetectorTrainingRun:
    encoder: RepresentationEncoder
    head: DetectorHead
    selection: EpochSelection
    representation_seed: int
    detector_seed: int


def train_base_detector_head(
    encoder: RepresentationEncoder,
    head: DetectorHead,
    training_population: tuple[TrainingObservation, ...],
    validation_population: tuple[TrainingObservation, ...],
    config: FedActConfig,
    seeds: PairedSeedIndex,
) -> BaseDetectorTrainingRun:
    apply_deterministic_torch_seed(seeds.detector_training_seed)
    loss_fn = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(
        head.parameters(),
        lr=config.training.initial_learning_rate,
        weight_decay=0.0,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=config.training.maximum_epochs, eta_min=config.training.final_learning_rate
    )

    def _evaluate(population: tuple[TrainingObservation, ...]) -> float:
        if not population:
            raise DetectorTrainingError("validation population must not be empty")
        encoder.eval()
        head.eval()
        with torch.no_grad():
            features = torch.tensor([item.features for item in population], dtype=torch.float32)
            labels = torch.tensor([[float(item.label)] for item in population], dtype=torch.float32)
            frozen = encoder(features).detach()
            logits = head(frozen)
            return float(loss_fn(logits, labels).item())

    history: list[float] = []
    batch_size = config.training.batch_size
    for _ in range(config.training.maximum_epochs):
        head.train()
        encoder.eval()
        with torch.no_grad():
            frozen = encoder(
                torch.tensor([item.features for item in training_population], dtype=torch.float32)
            ).detach()
        labels_all = torch.tensor(
            [[float(item.label)] for item in training_population], dtype=torch.float32
        )
        permutation = [int(index) for index in torch.randperm(len(training_population))]
        for start in range(0, len(permutation), batch_size):
            indices = permutation[start : start + batch_size]
            optimizer.zero_grad()
            loss = loss_fn(head(frozen[indices]), labels_all[indices])
            loss.backward()
            optimizer.step()
        scheduler.step()
        history.append(_evaluate(validation_population))
    selection = select_checkpoint_epoch(
        tuple(history),
        config.numerical.projection_tie_tolerance,
        config.training.early_stopping_patience_epochs,
    )
    return BaseDetectorTrainingRun(
        encoder=encoder,
        head=head,
        selection=selection,
        representation_seed=seeds.representation_seed,
        detector_seed=seeds.detector_training_seed,
    )
