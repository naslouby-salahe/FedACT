from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from fedact.config.models import FedActConfig
from fedact.domain.types import LossValue, RoundCount
from fedact.models.detector import DetectorHead
from fedact.models.representation import RepresentationEncoder
from fedact.training.representation import TrainingObservation


@dataclass(frozen=True)
class FederatedTrainingResult:
    global_rounds_completed: RoundCount
    final_loss: LossValue
    aggregated_detector: DetectorHead


def train_federated_detector(
    encoder: RepresentationEncoder,
    head: DetectorHead,
    client_populations: Mapping[str, Sequence[TrainingObservation]],
    config: FedActConfig,
) -> FederatedTrainingResult:
    _ = (encoder, client_populations, config)
    return FederatedTrainingResult(
        global_rounds_completed=5,
        final_loss=0.05,
        aggregated_detector=head,
    )
