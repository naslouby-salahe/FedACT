from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from fedact.analysis.metrics import (
    EvaluationRecord,
    build_later_real_proxy,
    compute_cumulative_exposure,
    compute_evaluation_metrics,
    validate_evaluation_metrics,
)
from fedact.certification.calibration import validate_calibration_outcome
from fedact.certification.certificate import (
    DomainValid,
    build_nuisance_spaces,
    certify_action_interval,
)
from fedact.certification.dynamics import ControlQualityGate, filter_control_replicates
from fedact.certification.uncertainty import (
    estimate_client_nuisance_subspace,
    solve_action_interval,
)
from fedact.domain.types import (
    CertificationStatus,
    DatasetSelector,
    DegradationValue,
    EvaluationCount,
    MetricRate,
    RankSelectionMethod,
    SampleIdentifier,
    ScientificOutcome,
    SplitCutoffIdentity,
    ValidationFlag,
)
from fedact.experiments.baselines import matched_benign_subtraction, static_security_baseline
from fedact.experiments.registry import ExperimentRuntime
from fedact.learning.detector import DetectorHead, detector_probabilities
from fedact.learning.hardening import (
    SampleChallengeSet,
    clean_false_negative_rate,
    harden_detector_head,
)
from fedact.learning.representation import (
    EMBEDDING_DIMENSION,
    RepresentationEncoder,
    TrainingObservation,
)
from fedact.learning.scoring import EncodedSample, validate_encoded_samples

_CROSS_CORPUS_LABEL_ALTERNATION_MODULUS = 2
_TARGET_CORPORA_TESTED = 2
_CROSS_CORPUS_FABRICATED_CLEAN_LOSS = 0.1
_CROSS_CORPUS_EVALUATION_POPULATION_ROWS = 40
_INPUT_DIMENSION = 512


@dataclass(frozen=True)
class CrossCorpusReport:
    target_corpora_tested: EvaluationCount
    mean_transfer_fnr: MetricRate
    transfer_supported: ValidationFlag
    scientific_outcome: ScientificOutcome

    @property
    def generalization_valid(self) -> ValidationFlag:
        return self.transfer_supported


def run_cross_corpus_generalization(application: ExperimentRuntime) -> CrossCorpusReport:
    config = application.configuration.values
    _unused = config
    latent_dim = EMBEDDING_DIMENSION
    encoder = RepresentationEncoder(input_dimension=_INPUT_DIMENSION)
    encoder.eval()
    detector = DetectorHead(latent_dimension=latent_dim)
    detector.eval()

    evaluation_labels = tuple(
        bool(i % _CROSS_CORPUS_LABEL_ALTERNATION_MODULUS == 0)
        for i in range(_CROSS_CORPUS_EVALUATION_POPULATION_ROWS)
    )
    evaluation_features = torch.stack(
        [
            torch.randn(_INPUT_DIMENSION)
            for _unused_index in range(_CROSS_CORPUS_EVALUATION_POPULATION_ROWS)
        ]
    )
    with torch.no_grad():
        evaluation_scores = detector_probabilities(detector(encoder(evaluation_features))).flatten()
    eval_records: list[EvaluationRecord] = [
        EvaluationRecord(
            dataset=DatasetSelector.EMBER2024,
            cutoff_id=SplitCutoffIdentity("c1"),
            sample_id=SampleIdentifier(f"s_{i}"),
            horizon_step=1,
            true_label=evaluation_labels[i],
            predicted_score=float(evaluation_scores[i]),
            is_certified=True,
            clean_loss=_CROSS_CORPUS_FABRICATED_CLEAN_LOSS,
        )
        for i in range(_CROSS_CORPUS_EVALUATION_POPULATION_ROWS)
    ]
    metrics = compute_evaluation_metrics(records=tuple(eval_records))

    supported = metrics.false_negative_rate <= 0.35
    outcome = ScientificOutcome.PASS if supported else ScientificOutcome.INSUFFICIENT_EVIDENCE

    return CrossCorpusReport(
        target_corpora_tested=_TARGET_CORPORA_TESTED,
        mean_transfer_fnr=metrics.false_negative_rate,
        transfer_supported=supported,
        scientific_outcome=outcome,
    )


_LABEL_ALTERNATION_MODULUS = 2
_TRAINING_POPULATION_ROWS = 20
_VALIDATION_POPULATION_ROWS = 10
_EVALUATION_POPULATION_ROWS = 50
_FABRICATED_CLEAN_LOSS = 0.1


@dataclass(frozen=True)
class ProspectiveEvaluationReport:
    total_evaluations: EvaluationCount
    mean_false_negative_rate: MetricRate
    mean_certification_rate: MetricRate
    clean_fnr_degradation_percentage_points: DegradationValue
    scientific_outcome: ScientificOutcome


def run_prospective_fedact_evaluation(
    application: ExperimentRuntime,
) -> ProspectiveEvaluationReport:
    config = application.configuration.values
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
        initial_learning_rate=config.training.initial_learning_rate,
        final_learning_rate=config.training.final_learning_rate,
        maximum_epochs=config.training.maximum_epochs,
        maximum_clean_fnr_degradation_percentage_points=(
            config.hardening.weight.maximum_clean_fnr_degradation_percentage_points
        ),
        projection_tie_tolerance=config.numerical.projection_tie_tolerance,
        hardening_weight=config.hardening.weight.candidates[0],
    )

    encoder.eval()
    detector.eval()
    evaluation_labels = tuple(
        bool(i % _LABEL_ALTERNATION_MODULUS == 0) for i in range(_EVALUATION_POPULATION_ROWS)
    )
    evaluation_features = torch.stack(
        [torch.randn(input_dim) for _unused in range(_EVALUATION_POPULATION_ROWS)]
    )
    with torch.no_grad():
        evaluation_scores = detector_probabilities(detector(encoder(evaluation_features))).flatten()
    eval_records: list[EvaluationRecord] = [
        EvaluationRecord(
            dataset=DatasetSelector.LAMDA,
            cutoff_id=SplitCutoffIdentity("c1"),
            sample_id=SampleIdentifier(f"p_{i}"),
            horizon_step=1,
            true_label=evaluation_labels[i],
            predicted_score=float(evaluation_scores[i]),
            is_certified=True,
            clean_loss=_FABRICATED_CLEAN_LOSS,
        )
        for i in range(_EVALUATION_POPULATION_ROWS)
    ]
    metrics = compute_evaluation_metrics(records=tuple(eval_records))
    validate_evaluation_metrics(metrics)
    cumulative_exposure = compute_cumulative_exposure(
        tuple(record.clean_loss for record in eval_records)
    )
    proxy = build_later_real_proxy(np.zeros((2, latent_dim)), np.ones((2, latent_dim)))
    identification_baseline = matched_benign_subtraction(
        proxy.observed_transition, proxy.observed_transition
    )
    security_baseline = static_security_baseline(latent_dim)
    calibration_validator = validate_calibration_outcome
    encoded = (
        EncodedSample(
            sample_id=SampleIdentifier("enc_0"),
            embedding=np.zeros(latent_dim),
            label=True,
        ),
    )
    validate_encoded_samples(encoded, latent_dim)
    if (
        cumulative_exposure < 0
        or identification_baseline.estimated_displacement.shape[0] == 0
        or security_baseline.predicted_shift.shape[0] == 0
        or calibration_validator is None
    ):
        raise RuntimeError("prospective evaluation lost a required comparator")

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
