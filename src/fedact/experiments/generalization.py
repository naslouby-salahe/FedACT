from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import torch

from fedact.analysis.metrics import EvaluationRecord, compute_evaluation_metrics
from fedact.data.lamda import (
    audited_label,
    label_derivation_rule,
    load_lamda_records,
    validate_lamda_dataset,
    year_month_to_calendar_month,
)
from fedact.domain.types import (
    DatasetSelector,
    DegradationValue,
    EvaluationCount,
    MetricRate,
    SampleIdentifier,
    ScientificOutcome,
    SplitCutoffIdentity,
    ValidationFlag,
)
from fedact.experiments.registry import ExperimentRuntime
from fedact.learning.detector import train_base_detector
from fedact.learning.hardening import (
    clean_false_negative_rate,
    harden_detector_head,
    read_challenge_sets,
)
from fedact.learning.representation import (
    DEFAULT_ENCODER_HIDDEN_DIMENSIONS,
    EMBEDDING_DIMENSION,
    RepresentationDataset,
    TrainingObservation,
    train_representation_encoder,
)
from fedact.learning.scoring import score_samples

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class CrossCorpusReport:
    target_corpora_tested: EvaluationCount
    mean_transfer_fnr: MetricRate
    transfer_supported: ValidationFlag
    scientific_outcome: ScientificOutcome

    @property
    def generalization_valid(self) -> ValidationFlag:
        return self.transfer_supported


@dataclass(frozen=True)
class ProspectiveEvaluationReport:
    total_evaluations: EvaluationCount
    mean_false_negative_rate: MetricRate
    mean_certification_rate: MetricRate
    clean_fnr_degradation_percentage_points: DegradationValue
    scientific_outcome: ScientificOutcome


@dataclass(frozen=True)
class _LamdaPopulation:
    features: np.ndarray
    labels: np.ndarray
    months: np.ndarray
    sample_ids: tuple[SampleIdentifier, ...]


def _load_lamda_population(application: ExperimentRuntime) -> _LamdaPopulation | None:
    raw_root = application.repository_root / "data" / "raw" / "LAMDA" / "Baseline" / "2023"
    if not raw_root.is_dir():
        LOGGER.warning("prospective evaluation has no LAMDA release at %s", raw_root)
        return None
    loaded = load_lamda_records(raw_root)
    validate_lamda_dataset(loaded)
    rule = label_derivation_rule(application.configuration.values.datasets.lamda)
    keep = np.fromiter(
        (audited_label(rule, record).binary_label is not None for record in loaded.records),
        dtype=bool,
        count=len(loaded.records),
    )
    if not np.any(keep):
        LOGGER.warning("LAMDA contains no rows with an auditable binary label")
        return None
    records = tuple(
        record for record, retained in zip(loaded.records, keep, strict=True) if retained
    )
    labels = np.fromiter(
        (bool(audited_label(rule, record).binary_label) for record in records),
        dtype=bool,
        count=len(records),
    )
    months = np.fromiter(
        (int(year_month_to_calendar_month(record.year_month)) for record in records),
        dtype=np.int64,
        count=len(records),
    )
    return _LamdaPopulation(
        features=np.ascontiguousarray(loaded.features[keep], dtype=np.float64),
        labels=labels,
        months=months,
        sample_ids=tuple(record.sample_hash for record in records),
    )


def _latest_eligible_cutoff(
    application: ExperimentRuntime, population: _LamdaPopulation
) -> int | None:
    config = application.configuration.values
    horizon = config.temporal.primary_confirmatory_horizon_months
    history = config.temporal.historical_training_window_months
    minimum = config.identification.minimum_support_per_class
    for cutoff in range(int(population.months.max()) - horizon, int(population.months.min()), -1):
        historical = (population.months >= cutoff - history) & (population.months < cutoff)
        later = (population.months >= cutoff) & (population.months < cutoff + horizon)
        if not historical.any() or not later.any():
            continue
        historical_labels = population.labels[historical]
        later_labels = population.labels[later]
        if (
            np.count_nonzero(historical_labels) >= minimum
            and np.count_nonzero(~historical_labels) >= minimum
            and np.count_nonzero(later_labels) > 0
            and np.count_nonzero(~later_labels) > 0
        ):
            return cutoff
    return None


def run_cross_corpus_generalization(application: ExperimentRuntime) -> CrossCorpusReport:
    source_checkpoint = (
        application.repository_root / "outputs" / "artifacts" / "models" / "lamda_locked.pt"
    )
    target_root = application.repository_root / "data" / "raw" / "EMBER2024"
    if not source_checkpoint.is_file() or not target_root.is_dir():
        LOGGER.warning(
            "cross-corpus transfer abstains: locked source checkpoint=%s target=%s",
            source_checkpoint.is_file(),
            target_root.is_dir(),
        )
        return CrossCorpusReport(0, 0.0, False, ScientificOutcome.INSUFFICIENT_EVIDENCE)
    LOGGER.warning("cross-corpus transfer requires a compatible locked feature adapter")
    return CrossCorpusReport(1, 0.0, False, ScientificOutcome.INSUFFICIENT_EVIDENCE)


def _score_cutoff_population(
    application: ExperimentRuntime,
    population: _LamdaPopulation,
    historical: np.ndarray,
    later: np.ndarray,
) -> tuple[tuple[SampleIdentifier, ...], tuple[float, ...]] | None:
    config = application.configuration.values
    observations = tuple(
        TrainingObservation(
            sample_id=sample_id,
            features=torch.tensor(feature, dtype=torch.float32),
            month_index=int(month),
            label=bool(label),
        )
        for sample_id, feature, month, label in zip(
            np.asarray(population.sample_ids, dtype=object)[historical],
            population.features[historical],
            population.months[historical],
            population.labels[historical],
            strict=True,
        )
    )
    validation_month = max(item.month_index for item in observations)
    training = tuple(item for item in observations if item.month_index < validation_month)
    validation = tuple(item for item in observations if item.month_index == validation_month)
    if not training or not validation:
        return None
    encoder, encoder_selection = train_representation_encoder(
        RepresentationDataset(training),
        RepresentationDataset(validation),
        population.features.shape[1],
        DEFAULT_ENCODER_HIDDEN_DIMENSIONS,
        EMBEDDING_DIMENSION,
        config.training.maximum_epochs,
        config.training.batch_size,
        config.training.initial_learning_rate,
        0.0,
        config.seeds.representation[0],
        config.numerical.projection_tie_tolerance,
    )
    LOGGER.info("selected representation checkpoint epoch=%s", encoder_selection.selected_epoch)
    detector = train_base_detector(
        encoder,
        RepresentationDataset(training).feature_tensor(),
        RepresentationDataset(training).label_tensor(),
        RepresentationDataset(validation).feature_tensor(),
        RepresentationDataset(validation).label_tensor(),
        config.training.maximum_epochs,
        config.training.batch_size,
        config.training.initial_learning_rate,
        0.0,
        config.seeds.representation[0],
        config.seeds.detector_training[0],
        config.numerical.projection_tie_tolerance,
    ).detector
    challenge_file = (
        application.repository_root
        / config.workspace.directories.experiments
        / "action-certificate-validation"
        / "challenges.json"
    )
    if challenge_file.is_file():
        challenges = read_challenge_sets(challenge_file)
        if challenges:
            detector = harden_detector_head(
                encoder,
                detector,
                training,
                validation,
                challenges,
                clean_false_negative_rate(detector, encoder, validation),
                config.training.initial_learning_rate,
                config.training.final_learning_rate,
                config.training.maximum_epochs,
                config.hardening.weight.maximum_clean_fnr_degradation_percentage_points,
                config.numerical.projection_tie_tolerance,
                config.hardening.weight.candidates[0],
            ).detector
    sample_ids = tuple(np.asarray(population.sample_ids, dtype=object)[later])
    scored = score_samples(
        encoder,
        detector,
        sample_ids,
        torch.tensor(population.features[later], dtype=torch.float32),
    )
    return sample_ids, tuple(score.probability for score in scored)


def run_prospective_fedact_evaluation(
    application: ExperimentRuntime,
) -> ProspectiveEvaluationReport:
    action_evidence = (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / "action-certificate-validation"
        / "actions.json"
    )
    if not action_evidence.is_file():
        LOGGER.warning("prospective evaluation requires completed action-certificate evidence")
        return ProspectiveEvaluationReport(
            0, 0.0, 0.0, 0.0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    population = _load_lamda_population(application)
    if population is None:
        return ProspectiveEvaluationReport(
            0, 0.0, 0.0, 0.0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    cutoff = _latest_eligible_cutoff(application, population)
    if cutoff is None:
        LOGGER.warning("no LAMDA cutoff satisfies configured history/support/horizon requirements")
        return ProspectiveEvaluationReport(
            0, 0.0, 0.0, 0.0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )

    config = application.configuration.values
    historical = (
        population.months >= cutoff - config.temporal.historical_training_window_months
    ) & (population.months < cutoff)
    later = (population.months >= cutoff) & (
        population.months < cutoff + config.temporal.primary_confirmatory_horizon_months
    )
    scored_population = _score_cutoff_population(application, population, historical, later)
    if scored_population is None:
        LOGGER.warning("cutoff has no disjoint chronological validation month")
        return ProspectiveEvaluationReport(
            0, 0.0, 0.0, 0.0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    sample_ids, scores = scored_population
    cutoff_id = SplitCutoffIdentity(f"lamda-{cutoff}")
    records = tuple(
        EvaluationRecord(
            dataset=DatasetSelector.LAMDA,
            cutoff_id=cutoff_id,
            sample_id=sample_id,
            horizon_step=1,
            true_label=bool(label),
            predicted_score=float(score),
            is_certified=False,
            clean_loss=0.0,
        )
        for sample_id, label, score in zip(
            sample_ids,
            population.labels[later],
            scores,
            strict=True,
        )
    )
    metrics = compute_evaluation_metrics(records)
    LOGGER.info("prospective baseline evaluated cutoff=%s rows=%s", cutoff_id, len(records))
    return ProspectiveEvaluationReport(
        total_evaluations=len(records),
        mean_false_negative_rate=metrics.false_negative_rate,
        mean_certification_rate=0.0,
        clean_fnr_degradation_percentage_points=0.0,
        scientific_outcome=ScientificOutcome.INSUFFICIENT_EVIDENCE,
    )
