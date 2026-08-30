from __future__ import annotations

import copy
import math
from collections.abc import Sequence
from dataclasses import dataclass

import torch
from torch.nn import functional as torch_functional

from fedact.config.models import FedActConfig
from fedact.domain.records import SampleIdentifier
from fedact.domain.types import (
    DegradationValue,
    EpochIndex,
    LossValue,
    MetricRate,
    ThresholdValue,
)
from fedact.models.detector import DetectorHead
from fedact.models.representation import RepresentationEncoder
from fedact.training.representation import EpochSelection, TrainingObservation


@dataclass(frozen=True)
class CleanFnr:
    rate: MetricRate


@dataclass(frozen=True)
class SampleChallengeSet:
    source_sample_id: SampleIdentifier
    challenge_embeddings: tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class HardeningResult:
    detector: DetectorHead
    selection: EpochSelection
    selected_epoch: EpochIndex
    clean_fnr_degradation_percentage_points: DegradationValue
    combined_validation_objective: LossValue


def clean_false_negative_rate(
    head: DetectorHead,
    encoder: RepresentationEncoder,
    validation_population: Sequence[TrainingObservation],
) -> CleanFnr:
    if not validation_population:
        return CleanFnr(rate=0.0)
    encoder.eval()
    head.eval()
    features = torch.stack(
        [
            torch.tensor(obs.features, dtype=torch.float32)
            if isinstance(obs.features, tuple)
            else obs.features
            for obs in validation_population
        ]
    )
    labels = torch.tensor([1 if obs.label else 0 for obs in validation_population])
    with torch.no_grad():
        encoded = encoder(features)
        logits = head(encoded)
        preds = logits >= 0.0
    positives = labels == 1
    if not positives.any():
        return CleanFnr(rate=0.0)
    fn = (positives & ~preds).sum().item()
    fnr = float(fn / positives.sum().item())
    return CleanFnr(rate=min(1.0, max(0.0, fnr)))


def _cosine_annealed_learning_rate(
    epoch_index: int,
    total_epochs: int,
    initial_rate: ThresholdValue,
    terminal_rate: ThresholdValue,
) -> float:
    if total_epochs <= 1:
        return float(terminal_rate)
    progress = epoch_index / (total_epochs - 1)
    return float(
        terminal_rate + 0.5 * (initial_rate - terminal_rate) * (1.0 + math.cos(math.pi * progress))
    )


def _historical_bce_loss(
    head: DetectorHead, embeddings: torch.Tensor, labels: torch.Tensor
) -> torch.Tensor:
    logits = head(embeddings).squeeze(-1)
    return torch_functional.binary_cross_entropy_with_logits(logits, labels)


def _worst_challenge_loss(
    head: DetectorHead,
    malicious_sample_ids: Sequence[SampleIdentifier],
    challenges_by_sample: dict[SampleIdentifier, tuple[tuple[float, ...], ...]],
) -> torch.Tensor | None:
    worst_losses: list[torch.Tensor] = []
    for sample_id in malicious_sample_ids:
        challenges = challenges_by_sample.get(sample_id, ())
        if not challenges:
            continue
        challenge_tensor = torch.tensor(challenges, dtype=torch.float32)
        challenge_logits = head(challenge_tensor).squeeze(-1)
        malicious_target = torch.ones_like(challenge_logits)
        challenge_losses = torch_functional.binary_cross_entropy_with_logits(
            challenge_logits, malicious_target, reduction="none"
        )
        worst_losses.append(challenge_losses.max())
    if not worst_losses:
        return None
    return torch.stack(worst_losses).mean()


def _combined_objective(
    head: DetectorHead,
    embeddings: torch.Tensor,
    labels: torch.Tensor,
    malicious_sample_ids: Sequence[SampleIdentifier],
    challenges_by_sample: dict[SampleIdentifier, tuple[tuple[float, ...], ...]],
    hardening_weight: ThresholdValue,
) -> torch.Tensor:
    historical = _historical_bce_loss(head, embeddings, labels)
    worst_challenge = _worst_challenge_loss(head, malicious_sample_ids, challenges_by_sample)
    if worst_challenge is None:
        return historical
    return historical + hardening_weight * worst_challenge


def harden_detector_head(
    encoder: RepresentationEncoder,
    head: DetectorHead,
    training_population: Sequence[TrainingObservation],
    validation_population: Sequence[TrainingObservation],
    challenge_sets: tuple[SampleChallengeSet, ...],
    baseline_clean_fnr: CleanFnr,
    config: FedActConfig,
    hardening_weight: ThresholdValue,
) -> HardeningResult:
    encoder.eval()
    challenges_by_sample = {
        challenge.source_sample_id: challenge.challenge_embeddings for challenge in challenge_sets
    }
    training_malicious_ids = tuple(
        observation.sample_id for observation in training_population if observation.label
    )

    train_features = torch.stack(
        [
            torch.tensor(obs.features, dtype=torch.float32)
            if isinstance(obs.features, tuple)
            else obs.features
            for obs in training_population
        ]
    )
    train_labels = torch.tensor(
        [1.0 if obs.label else 0.0 for obs in training_population], dtype=torch.float32
    )
    with torch.no_grad():
        train_embeddings = encoder(train_features)

    val_features = torch.stack(
        [
            torch.tensor(obs.features, dtype=torch.float32)
            if isinstance(obs.features, tuple)
            else obs.features
            for obs in validation_population
        ]
    )
    val_labels = torch.tensor(
        [1.0 if obs.label else 0.0 for obs in validation_population], dtype=torch.float32
    )
    validation_malicious_ids = tuple(
        observation.sample_id for observation in validation_population if observation.label
    )
    with torch.no_grad():
        val_embeddings = encoder(val_features)

    local_head = copy.deepcopy(head)
    optimizer = torch.optim.Adam(
        local_head.parameters(),
        lr=config.training.initial_learning_rate,
        weight_decay=0.0,
    )
    max_degradation = config.hardening.weight.maximum_clean_fnr_degradation_percentage_points
    total_epochs = config.training.maximum_epochs

    saved_states: list[dict[str, torch.Tensor]] = [
        {key: value.clone() for key, value in local_head.state_dict().items()}
    ]
    validation_objectives: list[float] = []
    degradations: list[DegradationValue] = [0.0]
    with torch.no_grad():
        local_head.eval()
        initial_objective = _combined_objective(
            local_head,
            val_embeddings,
            val_labels,
            validation_malicious_ids,
            challenges_by_sample,
            hardening_weight,
        )
    validation_objectives.append(float(initial_objective.item()))

    for epoch_index in range(total_epochs):
        learning_rate = _cosine_annealed_learning_rate(
            epoch_index,
            total_epochs,
            config.training.initial_learning_rate,
            config.training.final_learning_rate,
        )
        for group in optimizer.param_groups:
            group["lr"] = learning_rate
        local_head.train()
        optimizer.zero_grad()
        objective = _combined_objective(
            local_head,
            train_embeddings,
            train_labels,
            training_malicious_ids,
            challenges_by_sample,
            hardening_weight,
        )
        objective.backward()
        optimizer.step()

        local_head.eval()
        with torch.no_grad():
            validation_objective = _combined_objective(
                local_head,
                val_embeddings,
                val_labels,
                validation_malicious_ids,
                challenges_by_sample,
                hardening_weight,
            )
        epoch_fnr = clean_false_negative_rate(local_head, encoder, validation_population).rate
        degradation = max(0.0, (epoch_fnr - baseline_clean_fnr.rate) * 100.0)
        saved_states.append({key: value.clone() for key, value in local_head.state_dict().items()})
        validation_objectives.append(float(validation_objective.item()))
        degradations.append(degradation)

    eligible_epochs = [
        epoch for epoch, degradation in enumerate(degradations) if degradation <= max_degradation
    ]
    tolerance = config.numerical.projection_tie_tolerance
    best_epoch = eligible_epochs[0]
    best_objective = validation_objectives[best_epoch]
    for epoch in eligible_epochs[1:]:
        if validation_objectives[epoch] < best_objective - tolerance:
            best_objective = validation_objectives[epoch]
            best_epoch = epoch

    local_head.load_state_dict(saved_states[best_epoch])
    selection = EpochSelection(
        selected_epoch=best_epoch,
        selected_validation_loss=best_objective,
        eligible_epochs=len(eligible_epochs),
    )
    return HardeningResult(
        detector=local_head,
        selection=selection,
        selected_epoch=best_epoch,
        clean_fnr_degradation_percentage_points=degradations[best_epoch],
        combined_validation_objective=best_objective,
    )
