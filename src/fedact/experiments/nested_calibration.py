from __future__ import annotations

import torch

from fedact.calibration.nested import (
    CalibrationCandidate,
    HardeningWeightDegradation,
    HardeningWeightDegradations,
    generate_calibration_candidates,
)
from fedact.config.models import FedActConfig
from fedact.domain.records import SampleIdentifier
from fedact.domain.types import DegradationValue, DetailMessage, ThresholdValue
from fedact.models.detector import DetectorHead
from fedact.models.representation import EMBEDDING_DIMENSION, RepresentationEncoder
from fedact.training.hardening import (
    SampleChallengeSet,
    clean_false_negative_rate,
    harden_detector_head,
)
from fedact.training.representation import TrainingObservation

_INPUT_DIMENSION = 512
_TRAINING_POPULATION_ROWS = 20
_VALIDATION_POPULATION_ROWS = 10
_LABEL_ALTERNATION_MODULUS = 2


def _training_population(prefix: DetailMessage, size: int) -> tuple[TrainingObservation, ...]:
    return tuple(
        TrainingObservation(
            sample_id=SampleIdentifier(f"{prefix}_{i}"),
            features=torch.randn(_INPUT_DIMENSION),
            month_index=1,
            label=bool(i % _LABEL_ALTERNATION_MODULUS == 0),
        )
        for i in range(size)
    )


def _clean_degradation(config: FedActConfig, hardening_weight: ThresholdValue) -> DegradationValue:
    encoder = RepresentationEncoder(input_dimension=_INPUT_DIMENSION)
    detector = DetectorHead(latent_dimension=EMBEDDING_DIMENSION)
    train_population = _training_population("cal_t", _TRAINING_POPULATION_ROWS)
    validation_population = _training_population("cal_v", _VALIDATION_POPULATION_ROWS)
    challenges = (
        SampleChallengeSet(
            source_sample_id=train_population[0].sample_id,
            challenge_embeddings=(tuple(float(x) for x in torch.randn(EMBEDDING_DIMENSION)),),
        ),
    )
    baseline_clean_fnr = clean_false_negative_rate(detector, encoder, validation_population)
    hardening_result = harden_detector_head(
        encoder=encoder,
        head=detector,
        training_population=train_population,
        validation_population=validation_population,
        challenge_sets=challenges,
        baseline_clean_fnr=baseline_clean_fnr,
        config=config,
        hardening_weight=hardening_weight,
    )
    return hardening_result.clean_fnr_degradation_percentage_points


def run_nested_calibration(config: FedActConfig) -> tuple[CalibrationCandidate, ...]:
    weight_grid = tuple(config.hardening.weight.candidates)
    clean_degradations = HardeningWeightDegradations(
        entries=tuple(
            HardeningWeightDegradation(
                hardening_weight=weight, clean_degradation=_clean_degradation(config, weight)
            )
            for weight in weight_grid
        )
    )
    return generate_calibration_candidates(config, clean_degradations)
