from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import torch
from pydantic import Field
from torch import nn

from fedact.config.models import FedActConfig
from fedact.models.detector import DetectorHead
from fedact.models.representation import RepresentationEncoder
from fedact.training.representation import TrainingObservation

CleanFnr = Annotated[float, Field(ge=0.0, le=1.0)]
HardeningWeight = Annotated[float, Field(ge=0.0)]


class HardeningError(ValueError):
    pass


@dataclass(frozen=True)
class HardeningResult:
    selected_epoch: int
    clean_fnr_degradation_percentage_points: float
    combined_validation_objective: float


def clean_false_negative_rate(
    head: DetectorHead, encoder: RepresentationEncoder, population: tuple[TrainingObservation, ...]
) -> CleanFnr:
    malicious = [item for item in population if item.label]
    if not malicious:
        raise HardeningError("clean-cost evaluation requires malicious validation samples")
    encoder.eval()
    head.eval()
    with torch.no_grad():
        features = torch.tensor([item.features for item in malicious], dtype=torch.float32)
        scores = torch.sigmoid(head(encoder(features)).squeeze(dim=1))
    return float((scores < 0.5).float().mean().item())


def harden_detector_head(
    encoder: RepresentationEncoder,
    head: DetectorHead,
    training_population: tuple[TrainingObservation, ...],
    validation_population: tuple[TrainingObservation, ...],
    challenge_sets: dict[str, tuple[tuple[float, ...], ...]],
    baseline_clean_fnr: CleanFnr,
    config: FedActConfig,
    hardening_weight: HardeningWeight,
) -> HardeningResult:
    if not validation_population:
        raise HardeningError("hardening requires a cutoff-safe validation partition")
    loss_fn = nn.BCEWithLogitsLoss()
    optimizer = torch.optim.Adam(
        head.parameters(), lr=config.training.initial_learning_rate, weight_decay=0.0
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=config.training.maximum_epochs, eta_min=config.training.final_learning_rate
    )
    encoder.eval()
    with torch.no_grad():
        frozen_train = encoder(
            torch.tensor([item.features for item in training_population], dtype=torch.float32)
        ).detach()
        frozen_valid = encoder(
            torch.tensor([item.features for item in validation_population], dtype=torch.float32)
        ).detach()
    labels_train = torch.tensor(
        [[float(item.label)] for item in training_population], dtype=torch.float32
    )
    labels_valid = torch.tensor(
        [[float(item.label)] for item in validation_population], dtype=torch.float32
    )
    cap = config.hardening.maximum_actions_per_sample.primary
    allowed_fraction = (
        config.hardening.weight.maximum_clean_fnr_degradation_percentage_points / 100.0
    )
    best: HardeningResult | None = None
    for epoch in range(config.training.maximum_epochs):
        head.train()
        permutation = [int(index) for index in torch.randperm(len(training_population))]
        batch_size = config.training.batch_size
        for start in range(0, len(permutation), batch_size):
            indices = permutation[start : start + batch_size]
            optimizer.zero_grad()
            historical = loss_fn(head(frozen_train[indices]), labels_train[indices])
            adversarial_terms: list[torch.Tensor] = []
            for index in indices:
                sample_id = str(training_population[index].sample_id)
                challenges = challenge_sets.get(sample_id, ())[:cap]
                adversarial_terms.extend(
                    loss_fn(
                        head(torch.tensor([challenge], dtype=torch.float32)),
                        torch.ones((1, 1)),
                    )
                    for challenge in challenges
                )
            objective = (
                historical + hardening_weight * torch.stack(adversarial_terms).max()
                if adversarial_terms
                else historical
            )
            objective.backward()
            optimizer.step()
        scheduler.step()
        head.eval()
        with torch.no_grad():
            valid_loss = float(loss_fn(head(frozen_valid), labels_valid).item())
        degradation = max(
            0.0,
            clean_false_negative_rate(head, encoder, validation_population) - baseline_clean_fnr,
        )
        if degradation <= allowed_fraction:
            candidate = HardeningResult(
                selected_epoch=epoch,
                clean_fnr_degradation_percentage_points=degradation * 100.0,
                combined_validation_objective=valid_loss,
            )
            if (
                best is None
                or candidate.combined_validation_objective < best.combined_validation_objective
            ):
                best = candidate
    if best is None:
        raise HardeningError("no epoch satisfied the clean-cost constraint; hardening invalid")
    return best
