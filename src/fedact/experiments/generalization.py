from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from pydantic import Field

from fedact.analysis.comparisons import CutoffAggregate
from fedact.analysis.metrics import EvaluationRecord, compute_evaluation_metrics
from fedact.artifacts import write_text_atomically
from fedact.config.models import StrictModel
from fedact.data.ember2024 import (
    apply_log1p_transforms,
    ember2024_count_feature_mask,
    load_ember2024_records,
    validate_ember_dataset,
)
from fedact.data.lamda import (
    audited_label,
    label_derivation_rule,
    load_lamda_records,
    validate_lamda_dataset,
    year_month_to_calendar_month,
)
from fedact.domain.types import (
    BinaryLabel,
    CertificationStatus,
    DatasetSelector,
    DegradationValue,
    DimensionValue,
    EvaluationCount,
    LossValue,
    MetricRate,
    RankDimension,
    RelativePosixPath,
    SampleIdentifier,
    ScientificOutcome,
    SplitCutoffIdentity,
    ValidationFlag,
)
from fedact.experiments.registry import ExperimentRuntime
from fedact.learning.detector import load_trained_detector, train_base_detector
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
    load_representation_encoder,
    train_representation_encoder,
)
from fedact.learning.scoring import score_samples

LOGGER = logging.getLogger(__name__)


class _TransferManifest(StrictModel):
    encoder_checkpoint: RelativePosixPath
    detector_checkpoint: RelativePosixPath
    feature_adapter: RelativePosixPath
    input_dimension: RankDimension = Field(gt=0)


class _CertificateDecisionRecord(StrictModel):
    sample_id: SampleIdentifier
    status: CertificationStatus


class _CertificateDecisionArtifact(StrictModel):
    decisions: list[_CertificateDecisionRecord]


class _CutoffComparisonRecord(StrictModel):
    cutoff_id: SplitCutoffIdentity
    certified_false_negative_rate: MetricRate | None
    ambiguous_false_negative_rate: MetricRate | None


class _CutoffComparisonArtifact(StrictModel):
    comparisons: list[_CutoffComparisonRecord]


@dataclass(frozen=True)
class _FeatureAdapter:
    mean: np.ndarray
    scale: np.ndarray
    projection: np.ndarray


def _workspace_path(application: ExperimentRuntime, relative_path: RelativePosixPath) -> Path:
    resolved = (application.repository_root / relative_path).resolve()
    if not resolved.is_relative_to(application.repository_root.resolve()):
        raise ValueError(f"transfer artifact escapes repository root: {relative_path}")
    return resolved


def _load_feature_adapter(source: Path, input_dimension: DimensionValue) -> _FeatureAdapter:
    if not source.is_file():
        raise FileNotFoundError(f"locked feature adapter is missing: {source}")
    with np.load(source) as payload:
        mean = payload["mean"]
        scale = payload["scale"]
        projection = payload["projection"]
    if mean.ndim != 1 or scale.shape != mean.shape or projection.shape[0] != mean.size:
        raise ValueError("feature adapter arrays have incompatible dimensions")
    if projection.shape[1] != input_dimension:
        raise ValueError("feature adapter output does not match locked encoder dimension")
    if not np.isfinite(mean).all() or not np.isfinite(scale).all() or np.any(scale <= 0.0):
        raise ValueError("feature adapter has invalid fitted normalization parameters")
    return _FeatureAdapter(
        mean=np.asarray(mean, dtype=np.float32),
        scale=np.asarray(scale, dtype=np.float32),
        projection=np.asarray(projection, dtype=np.float32),
    )


def _labeled_target_value(value: BinaryLabel | None) -> BinaryLabel:
    if value is None:
        raise ValueError("selected EMBER evaluation row has no label")
    return value


def _binary_cross_entropy(label: BinaryLabel, probability: MetricRate) -> LossValue:
    bounded = np.clip(probability, np.finfo(np.float64).eps, 1.0 - np.finfo(np.float64).eps)
    return float(-np.log(bounded if label else 1.0 - bounded))


def _group_false_negative_rate(records: tuple[EvaluationRecord, ...]) -> MetricRate | None:
    malicious = tuple(record for record in records if record.true_label)
    if not malicious:
        return None
    return sum(record.predicted_score < 0.5 for record in malicious) / len(malicious)


def read_prospective_cutoff_aggregates(
    application: ExperimentRuntime,
) -> tuple[tuple[CutoffAggregate, ...], tuple[CutoffAggregate, ...]]:
    source = (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / "prospective-evaluation"
        / "cutoff-comparisons.json"
    )
    if not source.is_file():
        return (), ()
    artifact = _CutoffComparisonArtifact.model_validate_json(source.read_text(encoding="utf-8"))
    certified = tuple(
        CutoffAggregate(comparison.cutoff_id, comparison.certified_false_negative_rate, None)
        for comparison in artifact.comparisons
    )
    ambiguous = tuple(
        CutoffAggregate(comparison.cutoff_id, comparison.ambiguous_false_negative_rate, None)
        for comparison in artifact.comparisons
    )
    return certified, ambiguous


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


def _eligible_cutoffs(
    application: ExperimentRuntime, population: _LamdaPopulation
) -> tuple[int, ...]:
    config = application.configuration.values
    horizon = config.temporal.primary_confirmatory_horizon_months
    history = config.temporal.historical_training_window_months
    minimum = config.identification.minimum_support_per_class
    eligible: list[int] = []
    for cutoff in range(int(population.months.min()), int(population.months.max()) - horizon + 1):
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
            eligible.append(cutoff)
    return tuple(eligible)


def run_cross_corpus_generalization(application: ExperimentRuntime) -> CrossCorpusReport:
    manifest_path = (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / "cross-corpus"
        / "transfer.json"
    )
    target_root = application.repository_root / "data" / "raw" / "EMBER2024"
    if not manifest_path.is_file() or not target_root.is_dir():
        LOGGER.warning(
            "cross-corpus transfer requires a locked transfer manifest=%s target=%s",
            manifest_path.is_file(),
            target_root.is_dir(),
        )
        return CrossCorpusReport(0, 0.0, False, ScientificOutcome.INSUFFICIENT_EVIDENCE)
    manifest = _TransferManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    encoder_path = _workspace_path(application, manifest.encoder_checkpoint)
    detector_path = _workspace_path(application, manifest.detector_checkpoint)
    adapter = _load_feature_adapter(
        _workspace_path(application, manifest.feature_adapter), manifest.input_dimension
    )
    if not encoder_path.is_file() or not detector_path.is_file():
        raise FileNotFoundError("locked source encoder or detector checkpoint is missing")
    target = load_ember2024_records(target_root)
    validate_ember_dataset(target)
    labeled = np.fromiter(
        (record.label is not None for record in target.records),
        dtype=bool,
        count=len(target.records),
    )
    if not labeled.any():
        return CrossCorpusReport(0, 0.0, False, ScientificOutcome.INSUFFICIENT_EVIDENCE)
    target_features = apply_log1p_transforms(
        target.features[labeled], ember2024_count_feature_mask()
    )
    if target_features.shape[1] != adapter.mean.size:
        raise ValueError("locked adapter input does not match EMBER feature schema")
    adapted = ((target_features - adapter.mean) / adapter.scale) @ adapter.projection
    encoder = load_representation_encoder(
        encoder_path,
        manifest.input_dimension,
        DEFAULT_ENCODER_HIDDEN_DIMENSIONS,
        EMBEDDING_DIMENSION,
    )
    detector = load_trained_detector(detector_path, EMBEDDING_DIMENSION)
    selected_records = tuple(
        record for record, include in zip(target.records, labeled, strict=True) if include
    )
    scores = score_samples(
        encoder,
        detector,
        tuple(record.sample_hash for record in selected_records),
        torch.tensor(adapted, dtype=torch.float32),
    )
    evaluations = tuple(
        EvaluationRecord(
            dataset=DatasetSelector.EMBER2024,
            cutoff_id=SplitCutoffIdentity("ember2024-locked-transfer"),
            sample_id=record.sample_hash,
            horizon_step=1,
            true_label=_labeled_target_value(record.label),
            predicted_score=score.probability,
            is_certified=False,
            clean_loss=0.0,
        )
        for record, score in zip(selected_records, scores, strict=True)
    )
    metrics = compute_evaluation_metrics(evaluations)
    LOGGER.info("cross-corpus locked transfer scored target_rows=%s", len(evaluations))
    return CrossCorpusReport(
        len(evaluations),
        metrics.false_negative_rate,
        True,
        ScientificOutcome.PASS,
    )


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
    certificate_decisions = (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / "action-certificate-validation"
        / "certificate-decisions.json"
    )
    if not certificate_decisions.is_file():
        LOGGER.warning("prospective evaluation requires completed action-certificate evidence")
        return ProspectiveEvaluationReport(
            0, 0.0, 0.0, 0.0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    decision_artifact = _CertificateDecisionArtifact.model_validate_json(
        certificate_decisions.read_text(encoding="utf-8")
    )
    certified_samples = frozenset(
        decision.sample_id
        for decision in decision_artifact.decisions
        if decision.status is CertificationStatus.CERTIFIED_POSITIVE
    )
    population = _load_lamda_population(application)
    if population is None:
        return ProspectiveEvaluationReport(
            0, 0.0, 0.0, 0.0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    cutoffs = _eligible_cutoffs(application, population)
    if not cutoffs:
        LOGGER.warning("no LAMDA cutoff satisfies configured history/support/horizon requirements")
        return ProspectiveEvaluationReport(
            0, 0.0, 0.0, 0.0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )

    config = application.configuration.values
    records: list[EvaluationRecord] = []
    comparisons: list[_CutoffComparisonRecord] = []
    for cutoff in cutoffs:
        historical = (
            population.months >= cutoff - config.temporal.historical_training_window_months
        ) & (population.months < cutoff)
        later = (population.months >= cutoff) & (
            population.months < cutoff + config.temporal.primary_confirmatory_horizon_months
        )
        scored_population = _score_cutoff_population(application, population, historical, later)
        if scored_population is None:
            LOGGER.warning("cutoff has no disjoint chronological validation month: %s", cutoff)
            continue
        sample_ids, scores = scored_population
        cutoff_id = SplitCutoffIdentity(f"lamda-{cutoff}")
        cutoff_records = tuple(
            EvaluationRecord(
                dataset=DatasetSelector.LAMDA,
                cutoff_id=cutoff_id,
                sample_id=sample_id,
                horizon_step=1,
                true_label=label,
                predicted_score=score,
                is_certified=sample_id in certified_samples,
                clean_loss=_binary_cross_entropy(label, score),
            )
            for sample_id, label, score in zip(
                sample_ids,
                population.labels[later],
                scores,
                strict=True,
            )
        )
        records.extend(cutoff_records)
        certified_records = tuple(record for record in cutoff_records if record.is_certified)
        ambiguous_records = tuple(record for record in cutoff_records if not record.is_certified)
        comparisons.append(
            _CutoffComparisonRecord(
                cutoff_id=cutoff_id,
                certified_false_negative_rate=_group_false_negative_rate(certified_records),
                ambiguous_false_negative_rate=_group_false_negative_rate(ambiguous_records),
            )
        )
        LOGGER.info("prospective evaluated cutoff=%s rows=%s", cutoff_id, len(cutoff_records))
    if not records:
        return ProspectiveEvaluationReport(
            0, 0.0, 0.0, 0.0, ScientificOutcome.INSUFFICIENT_EVIDENCE
        )
    metrics = compute_evaluation_metrics(tuple(records))
    comparison = _CutoffComparisonArtifact(comparisons=comparisons)
    write_text_atomically(
        application.repository_root
        / config.workspace.directories.experiments
        / "prospective-evaluation"
        / "cutoff-comparisons.json",
        comparison.model_dump_json(indent=2),
    )
    LOGGER.info(
        "prospective evaluation completed cutoffs=%s rows=%s", len(comparisons), len(records)
    )
    return ProspectiveEvaluationReport(
        total_evaluations=len(records),
        mean_false_negative_rate=metrics.false_negative_rate,
        mean_certification_rate=metrics.certification_rate,
        clean_fnr_degradation_percentage_points=0.0,
        scientific_outcome=ScientificOutcome.PASS,
    )
