from __future__ import annotations

import torch

from fedact.config.loading import LoadedConfiguration
from fedact.domain.records import SampleIdentifier
from fedact.models.detector import DetectorHead
from fedact.models.representation import RepresentationEncoder
from fedact.training.hardening import (
    SampleChallengeSet,
    clean_false_negative_rate,
    harden_detector_head,
)
from fedact.training.representation import TrainingObservation


def test_harden_detector_head_runs_and_respects_clean_fnr_limit(
    production_configuration: LoadedConfiguration,
) -> None:
    torch.manual_seed(20260823)
    encoder = RepresentationEncoder(input_dimension=512)
    head = DetectorHead()
    train_pop = tuple(
        TrainingObservation(
            sample_id=SampleIdentifier(f"t_{i}"),
            month_index=i % 3,
            features=tuple(float(x) for x in torch.randn(512)),
            label=bool(i % 2 == 0),
        )
        for i in range(10)
    )
    val_pop = tuple(
        TrainingObservation(
            sample_id=SampleIdentifier(f"v_{i}"),
            month_index=i % 3,
            features=tuple(float(x) for x in torch.randn(512)),
            label=bool(i % 2 == 0),
        )
        for i in range(6)
    )
    challenges = (
        SampleChallengeSet(
            source_sample_id=SampleIdentifier("t_0"),
            challenge_embeddings=(tuple(0.5 for _ in range(64)),),
        ),
    )
    baseline_fnr = clean_false_negative_rate(head, encoder, val_pop)
    config = production_configuration.values
    result = harden_detector_head(
        encoder=encoder,
        head=head,
        training_population=train_pop,
        validation_population=val_pop,
        challenge_sets=challenges,
        baseline_clean_fnr=baseline_fnr,
        initial_learning_rate=config.training.initial_learning_rate,
        final_learning_rate=config.training.final_learning_rate,
        maximum_epochs=config.training.maximum_epochs,
        maximum_clean_fnr_degradation_percentage_points=(
            config.hardening.weight.maximum_clean_fnr_degradation_percentage_points
        ),
        projection_tie_tolerance=config.numerical.projection_tie_tolerance,
        hardening_weight=0.5,
    )
    assert result.selected_epoch >= 0
    assert result.clean_fnr_degradation_percentage_points <= 2.0
