from __future__ import annotations

import torch

from fedact.config.loading import LoadedConfiguration
from fedact.domain.records import SampleIdentifier
from fedact.models.detector import DetectorHead
from fedact.models.representation import RepresentationEncoder
from fedact.training.hardening import clean_false_negative_rate, harden_detector_head
from fedact.training.representation import TrainingObservation


def test_certificates_to_hardening_integration(
    production_configuration: LoadedConfiguration,
) -> None:
    torch.manual_seed(20260823)
    encoder = RepresentationEncoder(input_dimension=512)
    head = DetectorHead()
    train_pop = (
        TrainingObservation(
            sample_id=SampleIdentifier("s1"), month_index=0, features=(1.0,) * 512, label=True
        ),
        TrainingObservation(
            sample_id=SampleIdentifier("s2"), month_index=0, features=(0.0,) * 512, label=False
        ),
        TrainingObservation(
            sample_id=SampleIdentifier("s3"), month_index=0, features=(0.5,) * 512, label=True
        ),
    )
    val_pop = (
        TrainingObservation(
            sample_id=SampleIdentifier("v1"), month_index=0, features=(1.0,) * 512, label=True
        ),
        TrainingObservation(
            sample_id=SampleIdentifier("v2"), month_index=0, features=(0.0,) * 512, label=False
        ),
        TrainingObservation(
            sample_id=SampleIdentifier("v3"), month_index=0, features=(0.5,) * 512, label=True
        ),
    )
    challenges = {"s1": ((0.8,) * 64,)}
    baseline_fnr = clean_false_negative_rate(head, encoder, val_pop)
    result = harden_detector_head(
        encoder=encoder,
        head=head,
        training_population=train_pop,
        validation_population=val_pop,
        challenge_sets=challenges,
        baseline_clean_fnr=baseline_fnr,
        config=production_configuration.values,
        hardening_weight=0.5,
    )
    assert result.selected_epoch >= 0
