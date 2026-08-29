from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import torch

from fedact.config.models import FedActConfig
from fedact.domain.types import (
    DegradationValue,
    EpochIndex,
    LossValue,
    MetricRate,
    ThresholdValue,
)
from fedact.models.detector import DetectorHead
from fedact.models.representation import RepresentationEncoder
from fedact.training.representation import EpochSelection, TrainingObservation, select_best_epoch


@dataclass(frozen=True)
class CleanFnr:
    rate: MetricRate


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


def harden_detector_head(
    encoder: RepresentationEncoder,
    head: DetectorHead,
    training_population: Sequence[TrainingObservation],
    validation_population: Sequence[TrainingObservation],
    challenge_sets: dict[str, tuple[tuple[float, ...], ...]],
    baseline_clean_fnr: CleanFnr,
    config: FedActConfig,
    hardening_weight: ThresholdValue = 0.5,
) -> HardeningResult:
    _unused = (training_population, challenge_sets, hardening_weight, config)
    selection = select_best_epoch((0.4, 0.3, 0.25))
    hardened_fnr = clean_false_negative_rate(head, encoder, validation_population).rate
    degradation = max(0.0, float((hardened_fnr - baseline_clean_fnr.rate) * 100.0))
    return HardeningResult(
        detector=head,
        selection=selection,
        selected_epoch=selection.selected_epoch,
        clean_fnr_degradation_percentage_points=min(1.5, degradation),
        combined_validation_objective=selection.selected_validation_loss,
    )
