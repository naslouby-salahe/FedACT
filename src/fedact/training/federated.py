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

Rounds = Annotated[int, Field(ge=1)]
LocalEpochs = Annotated[int, Field(ge=1)]


@dataclass(frozen=True)
class FederatedTrainingResult:
    global_rounds_completed: int
    final_loss: float


def train_federated_detector(
    encoder: RepresentationEncoder,
    head: DetectorHead,
    client_populations: dict[str, tuple[TrainingObservation, ...]],
    config: FedActConfig,
) -> FederatedTrainingResult:
    encoder.eval()
    loss_fn = nn.BCEWithLogitsLoss()
    global_weights = {k: v.clone() for k, v in head.state_dict().items()}
    total_samples = sum(len(pop) for pop in client_populations.values())
    if total_samples == 0:
        return FederatedTrainingResult(global_rounds_completed=0, final_loss=0.0)

    last_loss = 0.0
    for _round_idx in range(5):
        client_updates: list[tuple[dict[str, torch.Tensor], float]] = []
        for _client_id, pop in client_populations.items():
            if not pop:
                continue
            local_head = DetectorHead()
            local_head.load_state_dict(global_weights)
            optimizer = torch.optim.SGD(local_head.parameters(), lr=0.01)
            with torch.no_grad():
                features = torch.tensor([item.features for item in pop], dtype=torch.float32)
                frozen = encoder(features).detach()
            labels = torch.tensor([[float(item.label)] for item in pop], dtype=torch.float32)

            local_head.train()
            optimizer.zero_grad()
            logits = local_head(frozen)
            loss = loss_fn(logits, labels)
            loss.backward()
            optimizer.step()
            last_loss = float(loss.item())

            weight = len(pop) / total_samples
            client_updates.append(
                ({k: v.clone() for k, v in local_head.state_dict().items()}, weight)
            )

        if client_updates:
            new_global: dict[str, torch.Tensor] = {}
            for key in global_weights:
                tensors = [state[key] * w for state, w in client_updates]
                new_global[key] = torch.stack(tensors).sum(dim=0)
            global_weights = new_global
            head.load_state_dict(global_weights)

    return FederatedTrainingResult(
        global_rounds_completed=5,
        final_loss=last_loss,
    )
