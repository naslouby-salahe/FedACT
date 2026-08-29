from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from torch.utils.data import DataLoader, TensorDataset

from fedact.domain.types import EpochIndex, RankDimension, SampleCount, SeedValue, ThresholdValue
from fedact.models.detector import DetectorHead
from fedact.models.representation import RepresentationEncoder
from fedact.training.representation import EpochSelection, select_best_epoch


@dataclass(frozen=True)
class BaseDetectorTrainingRun:
    detector: DetectorHead
    selection: EpochSelection
    representation_seed: SeedValue
    detector_seed: SeedValue


def train_base_detector(
    encoder: RepresentationEncoder,
    training_features: torch.Tensor,
    training_labels: torch.Tensor,
    validation_features: torch.Tensor,
    validation_labels: torch.Tensor,
    epochs: EpochIndex,
    batch_size: SampleCount,
    learning_rate: ThresholdValue,
    weight_decay: ThresholdValue,
    representation_seed: SeedValue,
    detector_seed: SeedValue,
) -> BaseDetectorTrainingRun:
    encoder.eval()
    with torch.no_grad():
        train_h = encoder(training_features)
        val_h = encoder(validation_features)
    torch.manual_seed(detector_seed)
    detector = DetectorHead(latent_dimension=train_h.shape[1])
    optimizer = torch.optim.Adam(detector.parameters(), lr=learning_rate, weight_decay=weight_decay)
    criterion = torch.nn.BCEWithLogitsLoss()
    dataset = TensorDataset(train_h, training_labels.float())
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0)
    val_losses: list[float] = []
    detector_states: list[dict[str, torch.Tensor]] = []
    for _unused in range(epochs):
        detector.train()
        for batch_h, batch_y in loader:
            optimizer.zero_grad()
            logits = detector(batch_h)
            loss = criterion(logits, batch_y)
            loss.backward()
            optimizer.step()
        detector.eval()
        with torch.no_grad():
            val_logits = detector(val_h)
            val_loss = float(criterion(val_logits, validation_labels.float()).item())
        val_losses.append(val_loss)
        detector_states.append({k: v.cpu().clone() for k, v in detector.state_dict().items()})
    selection = select_best_epoch(tuple(val_losses))
    detector.load_state_dict(detector_states[selection.selected_epoch])
    return BaseDetectorTrainingRun(
        detector=detector,
        selection=selection,
        representation_seed=representation_seed,
        detector_seed=detector_seed,
    )


def serialize_trained_detector(detector: DetectorHead, destination_path: Path) -> None:
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(detector.state_dict(), destination_path)


def load_trained_detector(source_path: Path, latent_dimension: RankDimension) -> DetectorHead:
    detector = DetectorHead(latent_dimension=latent_dimension)
    state = torch.load(source_path, weights_only=True)
    detector.load_state_dict(state)
    detector.eval()
    return detector


train_base_detector_head = train_base_detector
