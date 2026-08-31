from __future__ import annotations

import copy
import math
from dataclasses import dataclass

import torch
from torch.nn import functional as torch_functional

from fedact.domain.records import (
    ClientIdentifier,
    EpochIndex,
    LossValue,
    RoundCount,
    ThresholdValue,
)
from fedact.models.detector import DetectorHead
from fedact.models.representation import RepresentationEncoder
from fedact.training.representation import RepresentationDataset, TrainingObservation

_MINIMUM_LOCAL_BATCH_SIZE = 2
_COSINE_ANNEALING_HALF_RANGE = 0.5


@dataclass(frozen=True)
class ClientTrainingPopulation:
    client: ClientIdentifier
    observations: tuple[TrainingObservation, ...]


@dataclass(frozen=True)
class FederatedTrainingResult:
    global_rounds_completed: RoundCount
    final_loss: LossValue
    aggregated_detector: DetectorHead


def _cosine_annealed_learning_rate(
    round_index: int,
    total_rounds: int,
    initial_rate: ThresholdValue,
    terminal_rate: ThresholdValue,
) -> float:
    if total_rounds <= 1:
        return float(terminal_rate)
    progress = round_index / (total_rounds - 1)
    return float(
        terminal_rate
        + _COSINE_ANNEALING_HALF_RANGE
        * (initial_rate - terminal_rate)
        * (1.0 + math.cos(math.pi * progress))
    )


def _local_epoch(
    encoder_template: RepresentationEncoder,
    head_template: DetectorHead,
    encoder_state: dict[str, torch.Tensor],
    head_state: dict[str, torch.Tensor],
    population: ClientTrainingPopulation,
    learning_rate: float,
) -> tuple[dict[str, torch.Tensor], dict[str, torch.Tensor], float]:
    local_encoder = copy.deepcopy(encoder_template)
    local_head = copy.deepcopy(head_template)
    local_encoder.load_state_dict(encoder_state)
    local_head.load_state_dict(head_state)
    dataset = RepresentationDataset(population.observations)
    features = dataset.feature_tensor()
    labels = dataset.label_tensor().float()
    optimizer = torch.optim.Adam(
        list(local_encoder.parameters()) + list(local_head.parameters()),
        lr=learning_rate,
        weight_decay=0.0,
    )
    local_encoder.train()
    local_head.train()
    optimizer.zero_grad()
    logits = local_head(local_encoder(features)).squeeze(-1)
    loss = torch_functional.binary_cross_entropy_with_logits(logits, labels)
    loss.backward()
    optimizer.step()
    return local_encoder.state_dict(), local_head.state_dict(), float(loss.item())


def _weighted_average_state(
    weighted_states: list[tuple[int, dict[str, torch.Tensor]]], total_samples: int
) -> dict[str, torch.Tensor]:
    keys = weighted_states[0][1].keys()
    averaged: dict[str, torch.Tensor] = {}
    for key in keys:
        accumulator = torch.zeros_like(weighted_states[0][1][key], dtype=torch.float32)
        for weight, state in weighted_states:
            accumulator += (float(weight) / total_samples) * state[key]
        averaged[key] = accumulator
    return averaged


def train_federated_detector(
    encoder: RepresentationEncoder,
    head: DetectorHead,
    client_populations: tuple[ClientTrainingPopulation, ...],
    maximum_rounds: EpochIndex,
    initial_learning_rate: ThresholdValue,
    final_learning_rate: ThresholdValue,
) -> FederatedTrainingResult:
    eligible_populations = tuple(
        population
        for population in client_populations
        if len(population.observations) >= _MINIMUM_LOCAL_BATCH_SIZE
    )
    total_rounds = maximum_rounds
    encoder_state = {key: value.clone() for key, value in encoder.state_dict().items()}
    head_state = {key: value.clone() for key, value in head.state_dict().items()}
    final_loss: LossValue = 0.0
    completed_rounds = 0
    for round_index in range(total_rounds):
        learning_rate = _cosine_annealed_learning_rate(
            round_index,
            total_rounds,
            initial_learning_rate,
            final_learning_rate,
        )
        weighted_encoder_states: list[tuple[int, dict[str, torch.Tensor]]] = []
        weighted_head_states: list[tuple[int, dict[str, torch.Tensor]]] = []
        total_samples = 0
        round_losses: list[float] = []
        for population in eligible_populations:
            local_encoder_state, local_head_state, loss = _local_epoch(
                encoder, head, encoder_state, head_state, population, learning_rate
            )
            sample_count = len(population.observations)
            weighted_encoder_states.append((sample_count, local_encoder_state))
            weighted_head_states.append((sample_count, local_head_state))
            total_samples += sample_count
            round_losses.append(loss)
        if total_samples == 0:
            break
        encoder_state = _weighted_average_state(weighted_encoder_states, total_samples)
        head_state = _weighted_average_state(weighted_head_states, total_samples)
        final_loss = sum(round_losses) / len(round_losses)
        completed_rounds += 1

    encoder.load_state_dict(encoder_state)
    head.load_state_dict(head_state)
    return FederatedTrainingResult(
        global_rounds_completed=completed_rounds,
        final_loss=final_loss,
        aggregated_detector=head,
    )
