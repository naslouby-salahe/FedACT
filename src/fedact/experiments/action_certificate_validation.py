from __future__ import annotations

from dataclasses import dataclass

import torch

from fedact.app import Application
from fedact.calibration.nested import (
    CalibrationCandidate,
    HardeningWeightDegradation,
    HardeningWeightDegradations,
    generate_calibration_candidates,
)
from fedact.core.certification import DomainValid, certify_action_interval
from fedact.core.feasible_sets import build_nuisance_spaces
from fedact.core.nuisance import estimate_client_nuisance_subspace
from fedact.core.solver import solve_action_interval
from fedact.domain.enums import CertificationStatus, RankSelectionMethod, ScientificOutcome
from fedact.domain.records import (
    DegradationValue,
    DetailMessage,
    EvaluationCount,
    MetricRate,
    SampleIdentifier,
    ThresholdValue,
)
from fedact.models.detector import DetectorHead
from fedact.models.representation import EMBEDDING_DIMENSION, RepresentationEncoder
from fedact.training.hardening import (
    SampleChallengeSet,
    clean_false_negative_rate,
    harden_detector_head,
)
from fedact.training.representation import TrainingObservation

_ACTION_MAGNITUDE = 2.0


@dataclass(frozen=True)
class ActionCertificateReport:
    total_actions: EvaluationCount
    certified_positive_count: EvaluationCount
    ambiguous_count: EvaluationCount
    abstention_count: EvaluationCount
    coverage_rate: MetricRate
    scientific_outcome: ScientificOutcome


def run_action_certificate_validation(application: Application) -> ActionCertificateReport:

    config = application.configuration.values
    latent_dim = 64
    nuisance_estimates = [
        estimate_client_nuisance_subspace(
            client_controls=torch.randn(20, latent_dim),
            rank_selection=RankSelectionMethod.FIXED_RANK,
            fixed_rank=config.identification.nuisance_rank.maximum,
            eigengap_regularization=config.numerical.rank_clip_epsilon_relative,
            scale_standardization_floor=config.numerical.scale_standardization_floor,
        )
        for _unused in range(5)
    ]
    feasible_set = build_nuisance_spaces(
        nuisance_subspaces=tuple(e.subspace for e in nuisance_estimates),
        uncertainty_radii=tuple(0.01 for _unused in nuisance_estimates),
    )
    actions = [torch.ones(latent_dim) * _ACTION_MAGNITUDE for _unused in range(50)]

    certified = 0
    ambiguous = 0
    abstained = 0

    for action in actions:
        interval = solve_action_interval(action_vector=action, feasible_set=feasible_set)
        decision = certify_action_interval(
            action_interval=interval,
            domain_validity=DomainValid(valid=True),
            alignment_threshold=0.01,
            ambiguity_width_threshold=5.0,
            set_diameter=feasible_set.diameter,
            historical_realized_diameter_quantile=(
                config.certification.forecast_set_diameter_abstention.historical_realized_diameter_quantile
            ),
        )
        if decision.status is CertificationStatus.CERTIFIED_POSITIVE:
            certified += 1
        elif decision.status is CertificationStatus.AMBIGUOUS:
            ambiguous += 1
        else:
            abstained += 1

    coverage = (certified + ambiguous) / max(1, len(actions))
    outcome = (
        ScientificOutcome.PASS
        if certified > 0 and abstained < len(actions)
        else ScientificOutcome.INSUFFICIENT_EVIDENCE
    )

    return ActionCertificateReport(
        total_actions=len(actions),
        certified_positive_count=certified,
        ambiguous_count=ambiguous,
        abstention_count=abstained,
        coverage_rate=coverage,
        scientific_outcome=outcome,
    )


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


def _clean_degradation(
    application: Application, hardening_weight: ThresholdValue
) -> DegradationValue:
    config = application.configuration.values
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
        initial_learning_rate=config.training.initial_learning_rate,
        final_learning_rate=config.training.final_learning_rate,
        maximum_epochs=config.training.maximum_epochs,
        maximum_clean_fnr_degradation_percentage_points=(
            config.hardening.weight.maximum_clean_fnr_degradation_percentage_points
        ),
        projection_tie_tolerance=config.numerical.projection_tie_tolerance,
        hardening_weight=hardening_weight,
    )
    return hardening_result.clean_fnr_degradation_percentage_points


def run_nested_calibration(application: Application) -> tuple[CalibrationCandidate, ...]:
    config = application.configuration.values
    weight_grid = tuple(config.hardening.weight.candidates)
    clean_degradations = HardeningWeightDegradations(
        entries=tuple(
            HardeningWeightDegradation(
                hardening_weight=weight,
                clean_degradation=_clean_degradation(application, weight),
            )
            for weight in weight_grid
        )
    )
    return generate_calibration_candidates(
        alignment_percentile_candidates=tuple(
            config.certification.alignment_threshold.percentile_candidates
        ),
        ambiguity_width_percentile_candidates=tuple(
            config.certification.ambiguity_width.percentile_candidates
        ),
        hardening_weight_candidates=weight_grid,
        maximum_nuisance_rank=config.identification.nuisance_rank.maximum,
        eigengap_regularization=config.numerical.rank_clip_epsilon_relative,
        scale_standardization_floor=config.numerical.scale_standardization_floor,
        historical_realized_diameter_quantile=(
            config.certification.forecast_set_diameter_abstention.historical_realized_diameter_quantile
        ),
        clean_degradations=clean_degradations,
    )
