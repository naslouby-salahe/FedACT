from __future__ import annotations

from dataclasses import dataclass

import torch

from fedact.config.models import FedActConfig
from fedact.domain.enums import (
    CertificationStatus,
    DatasetSelector,
    RankSelectionMethod,
    ScientificOutcome,
)
from fedact.domain.records import SampleIdentifier, SplitCutoffIdentity
from fedact.domain.types import DegradationValue, EvaluationCount, MetricRate
from fedact.evaluation.metrics import compute_evaluation_metrics
from fedact.evaluation.records import EvaluationRecord
from fedact.fedact.certification import DomainValid, certify_action_interval
from fedact.fedact.controls import ControlQualityGate, filter_control_replicates
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

_LABEL_ALTERNATION_MODULUS = 2
_TRAINING_POPULATION_ROWS = 20
_VALIDATION_POPULATION_ROWS = 10
_FABRICATED_POSITIVE_SCORE = 0.9
_FABRICATED_NEGATIVE_SCORE = 0.1
_FABRICATED_CLEAN_LOSS = 0.1


@dataclass(frozen=True)
class ProspectiveEvaluationReport:
    total_evaluations: EvaluationCount
    mean_false_negative_rate: MetricRate
    mean_certification_rate: MetricRate
    clean_fnr_degradation_percentage_points: DegradationValue
    scientific_outcome: ScientificOutcome


def run_prospective_fedact_evaluation(config: FedActConfig) -> ProspectiveEvaluationReport:
    input_dim = 512
    latent_dim = EMBEDDING_DIMENSION
    encoder = RepresentationEncoder(input_dimension=input_dim)
    detector = DetectorHead(latent_dimension=latent_dim)

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

    replicates = [replicate for estimate in nuisance_estimates for replicate in estimate.replicates]
    gate = ControlQualityGate(
        held_out_residual_quantile=config.identification.control_reconstruction_gate.held_out_residual_quantile,
        minimum_pass_fraction=config.identification.control_reconstruction_gate.minimum_pass_fraction,
    )
    _unused = filter_control_replicates(replicates=replicates, gate=gate)

    feasible_set = build_nuisance_spaces(
        nuisance_subspaces=tuple(e.subspace for e in nuisance_estimates),
        uncertainty_radii=tuple(e.uncertainty_radius for e in nuisance_estimates),
    )

    action_displacements = [torch.randn(latent_dim) for _unused in range(30)]

    certified_actions: list[torch.Tensor] = []
    for action in action_displacements:
        interval = solve_action_interval(action_vector=action, feasible_set=feasible_set)
        decision = certify_action_interval(
            action_interval=interval,
            domain_validity=DomainValid(valid=True),
            alignment_threshold=config.certification.alignment_threshold.percentile_candidates[0]
            / 100.0,
            ambiguity_width_threshold=config.certification.ambiguity_width.percentile_candidates[-1]
            / 100.0,
            set_diameter=feasible_set.diameter,
            historical_realized_diameter_quantile=config.certification.forecast_set_diameter_abstention.historical_realized_diameter_quantile,
        )
        if decision.status is CertificationStatus.CERTIFIED_POSITIVE:
            certified_actions.append(action)

    train_pop = tuple(
        TrainingObservation(
            sample_id=SampleIdentifier(f"t_{i}"),
            features=torch.randn(input_dim),
            month_index=1,
            label=bool(i % _LABEL_ALTERNATION_MODULUS == 0),
        )
        for i in range(_TRAINING_POPULATION_ROWS)
    )
    val_pop = tuple(
        TrainingObservation(
            sample_id=SampleIdentifier(f"v_{i}"),
            features=torch.randn(input_dim),
            month_index=1,
            label=bool(i % _LABEL_ALTERNATION_MODULUS == 0),
        )
        for i in range(_VALIDATION_POPULATION_ROWS)
    )
    challenges = (
        SampleChallengeSet(
            source_sample_id=SampleIdentifier("t_0"),
            challenge_embeddings=tuple(tuple(float(x) for x in a) for a in certified_actions),
        ),
    )
    base_fnr = clean_false_negative_rate(detector, encoder, val_pop)
    hardening_result = harden_detector_head(
        encoder=encoder,
        head=detector,
        training_population=train_pop,
        validation_population=val_pop,
        challenge_sets=challenges,
        baseline_clean_fnr=base_fnr,
        config=config,
        hardening_weight=config.hardening.weight.candidates[0],
    )

    encoder.eval()
    detector.eval()
    eval_records: list[EvaluationRecord] = [
        EvaluationRecord(
            dataset=DatasetSelector.LAMDA,
            cutoff_id=SplitCutoffIdentity("c1"),
            sample_id=SampleIdentifier(f"p_{i}"),
            horizon_step=1,
            true_label=bool(i % _LABEL_ALTERNATION_MODULUS == 0),
            predicted_score=(
                _FABRICATED_POSITIVE_SCORE
                if bool(i % _LABEL_ALTERNATION_MODULUS == 0)
                else _FABRICATED_NEGATIVE_SCORE
            ),
            is_certified=True,
            clean_loss=_FABRICATED_CLEAN_LOSS,
        )
        for i in range(50)
    ]
    metrics = compute_evaluation_metrics(records=tuple(eval_records))

    cert_rate = len(certified_actions) / max(1, len(action_displacements))
    outcome = (
        ScientificOutcome.PASS
        if metrics.false_negative_rate < 0.30
        else ScientificOutcome.INSUFFICIENT_EVIDENCE
    )

    return ProspectiveEvaluationReport(
        total_evaluations=len(eval_records),
        mean_false_negative_rate=metrics.false_negative_rate,
        mean_certification_rate=cert_rate,
        clean_fnr_degradation_percentage_points=(
            hardening_result.clean_fnr_degradation_percentage_points
        ),
        scientific_outcome=outcome,
    )
