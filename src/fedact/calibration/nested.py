from __future__ import annotations

from dataclasses import dataclass

import torch

from fedact.config.models import FedActConfig
from fedact.domain.enums import CertificationStatus, RankSelectionMethod
from fedact.domain.records import (
    DegradationValue,
    DetailMessage,
    MetricRate,
    SampleIdentifier,
    ThresholdValue,
)
from fedact.fedact.certification import DomainValid, certify_action_interval
from fedact.fedact.feasible_sets import build_nuisance_spaces
from fedact.fedact.nuisance import estimate_client_nuisance_subspace
from fedact.fedact.solver import solve_action_interval
from fedact.models.detector import DetectorHead
from fedact.models.representation import EMBEDDING_DIMENSION, RepresentationEncoder
from fedact.training.hardening import (
    SampleChallengeSet,
    clean_false_negative_rate,
    harden_detector_head,
)
from fedact.training.representation import TrainingObservation

_CLIENT_CONTROL_ROWS = 20
_CERTIFICATION_DRAW_COUNT = 30


@dataclass(frozen=True)
class HardeningWeightDegradation:
    hardening_weight: ThresholdValue
    clean_degradation: DegradationValue


@dataclass(frozen=True)
class HardeningWeightDegradations:
    entries: tuple[HardeningWeightDegradation, ...]

    def for_weight(self, hardening_weight: ThresholdValue) -> DegradationValue:
        for entry in self.entries:
            if entry.hardening_weight == hardening_weight:
                return entry.clean_degradation
        raise KeyError(f"no clean degradation recorded for hardening weight {hardening_weight}")


@dataclass(frozen=True)
class CalibrationCandidate:
    candidate_id: DetailMessage
    tau_align: ThresholdValue
    tau_amb: ThresholdValue
    hardening_weight: ThresholdValue
    observed_coverage: MetricRate
    observed_certification_rate: MetricRate
    clean_degradation: DegradationValue


def _certification_rate(
    config: FedActConfig, tau_align: ThresholdValue, tau_amb: ThresholdValue
) -> MetricRate:
    latent_dim = EMBEDDING_DIMENSION
    estimate = estimate_client_nuisance_subspace(
        client_controls=torch.randn(_CLIENT_CONTROL_ROWS, latent_dim),
        rank_selection=RankSelectionMethod.FIXED_RANK,
        fixed_rank=config.identification.nuisance_rank.maximum,
        eigengap_regularization=config.numerical.rank_clip_epsilon_relative,
        scale_standardization_floor=config.numerical.scale_standardization_floor,
    )
    feasible_set = build_nuisance_spaces(
        nuisance_subspaces=(estimate.subspace,),
        uncertainty_radii=(estimate.uncertainty_radius,),
    )
    certified = 0
    for _unused in range(_CERTIFICATION_DRAW_COUNT):
        action = torch.randn(latent_dim)
        interval = solve_action_interval(action_vector=action, feasible_set=feasible_set)
        decision = certify_action_interval(
            action_interval=interval,
            domain_validity=DomainValid(valid=True),
            alignment_threshold=tau_align,
            ambiguity_width_threshold=tau_amb,
            set_diameter=feasible_set.diameter,
            historical_realized_diameter_quantile=(
                config.certification.forecast_set_diameter_abstention.historical_realized_diameter_quantile
            ),
        )
        if decision.status is CertificationStatus.CERTIFIED_POSITIVE:
            certified += 1
    return certified / _CERTIFICATION_DRAW_COUNT


def generate_calibration_candidates(
    config: FedActConfig,
    clean_degradations: HardeningWeightDegradations,
) -> tuple[CalibrationCandidate, ...]:
    align_grid = tuple(
        value / 100.0 for value in config.certification.alignment_threshold.percentile_candidates
    )
    ambiguity_grid = tuple(
        value / 100.0 for value in config.certification.ambiguity_width.percentile_candidates
    )
    weight_grid = tuple(config.hardening.weight.candidates)

    certification_rates = {
        (tau_align, tau_amb): _certification_rate(config, tau_align, tau_amb)
        for tau_align in align_grid
        for tau_amb in ambiguity_grid
    }

    candidates: list[CalibrationCandidate] = []
    idx = 0
    for tau_align in align_grid:
        for tau_amb in ambiguity_grid:
            rate = certification_rates[(tau_align, tau_amb)]
            for weight in weight_grid:
                candidates.append(
                    CalibrationCandidate(
                        candidate_id=f"cand_{idx}",
                        tau_align=tau_align,
                        tau_amb=tau_amb,
                        hardening_weight=weight,
                        observed_coverage=rate,
                        observed_certification_rate=rate,
                        clean_degradation=clean_degradations.for_weight(weight),
                    )
                )
                idx += 1
    return tuple(candidates)


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
