from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fedact.domain.enums import (
    ArtifactBoundary,
    DatasetSplit,
    InformationFlowPhase,
    PartitionScheme,
    WorkflowName,
)
from fedact.domain.records import DependencyFingerprint
from fedact.domain.types import ArtifactName, EpochIndex, TriggerabilityFlag, WorkflowDescription


class SharedProducer(StrEnum):
    REPRESENTATION_DETECTOR_FIT = "representation_detector_fit"
    ENCODING_SCORING_AND_SUMMARIES = "encoding_scoring_and_summaries"
    NESTED_PRE_CUTOFF_CALIBRATION = "nested_pre_cutoff_calibration"
    BASELINE_FIT_PARITY = "baseline_fit_parity"


class OverwriteRequest:
    def __init__(self, requested: bool = False) -> None:
        self.requested = requested


class ReuseDecision(StrEnum):
    REUSE = "REUSE"
    STALE = "STALE"
    OVERWRITE = "OVERWRITE"
    RECOMPUTE = "RECOMPUTE"


@dataclass(frozen=True)
class PreprocessStage:
    stage_order: EpochIndex
    name: ArtifactName
    boundary: ArtifactBoundary
    scope: WorkflowDescription


@dataclass(frozen=True)
class ProducerOwnership:
    boundary: ArtifactBoundary
    sole_producer: WorkflowName
    reuse_scope: WorkflowDescription
    phase: InformationFlowPhase
    partition_scheme: PartitionScheme
    split_eligibility: tuple[DatasetSplit, ...]

    @property
    def producer(self) -> WorkflowName:
        return self.sole_producer


PREPROCESS_STAGE_FLOW: tuple[PreprocessStage, ...] = (
    PreprocessStage(
        stage_order=1,
        name="raw discovery/checksum",
        boundary=ArtifactBoundary.DATASET_PREPARATION,
        scope="raw-data-manifests",
    ),
    PreprocessStage(
        stage_order=2,
        name="normalized parsed preparation",
        boundary=ArtifactBoundary.DATASET_PREPARATION,
        scope="parsed-samples",
    ),
    PreprocessStage(
        stage_order=3,
        name="chronology/cutoff construction",
        boundary=ArtifactBoundary.PREPROCESSING_AND_SPLITS,
        scope="chronological-and-federated-splits",
    ),
    PreprocessStage(
        stage_order=4,
        name="real-data audits",
        boundary=ArtifactBoundary.PREPROCESSING_AND_SPLITS,
        scope="audit-manifests",
    ),
)


PREPROCESS_OWNED_BOUNDARIES: dict[ArtifactBoundary, ProducerOwnership] = {
    ArtifactBoundary.DATASET_PREPARATION: ProducerOwnership(
        boundary=ArtifactBoundary.DATASET_PREPARATION,
        sole_producer=WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT,
        reuse_scope="§9.5 raw-data-manifests",
        phase=InformationFlowPhase.PREPROCESSING,
        partition_scheme=PartitionScheme.CHRONOLOGICAL,
        split_eligibility=(DatasetSplit.HISTORICAL, DatasetSplit.PROSPECTIVE),
    ),
    ArtifactBoundary.PREPROCESSING_AND_SPLITS: ProducerOwnership(
        boundary=ArtifactBoundary.PREPROCESSING_AND_SPLITS,
        sole_producer=WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT,
        reuse_scope="preprocessing-and-splits",
        phase=InformationFlowPhase.PREPROCESSING,
        partition_scheme=PartitionScheme.FEDERATED,
        split_eligibility=(DatasetSplit.HISTORICAL, DatasetSplit.PROSPECTIVE),
    ),
}


SHARED_PRODUCER_REGISTRY: dict[SharedProducer, ProducerOwnership] = {
    SharedProducer.REPRESENTATION_DETECTOR_FIT: ProducerOwnership(
        boundary=ArtifactBoundary.TRAINING_CHECKPOINTS,
        sole_producer=WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION,
        reuse_scope="§9.5 representation and base detector fit",
        phase=InformationFlowPhase.HISTORICAL_CALIBRATION,
        partition_scheme=PartitionScheme.CHRONOLOGICAL,
        split_eligibility=(DatasetSplit.HISTORICAL,),
    ),
    SharedProducer.ENCODING_SCORING_AND_SUMMARIES: ProducerOwnership(
        boundary=ArtifactBoundary.SCORING_AND_SUMMARIES,
        sole_producer=WorkflowName.NESTED_PRE_CUTOFF_CALIBRATION,
        reuse_scope="same checkpoint encoded and scored observations",
        phase=InformationFlowPhase.HISTORICAL_CALIBRATION,
        partition_scheme=PartitionScheme.FEDERATED,
        split_eligibility=(DatasetSplit.HISTORICAL,),
    ),
    SharedProducer.NESTED_PRE_CUTOFF_CALIBRATION: ProducerOwnership(
        boundary=ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
        sole_producer=WorkflowName.NESTED_PRE_CUTOFF_CALIBRATION,
        reuse_scope="dataset/cutoff nested pre-cutoff calibration",
        phase=InformationFlowPhase.HISTORICAL_CALIBRATION,
        partition_scheme=PartitionScheme.FEDERATED,
        split_eligibility=(DatasetSplit.HISTORICAL,),
    ),
    SharedProducer.BASELINE_FIT_PARITY: ProducerOwnership(
        boundary=ArtifactBoundary.TRAINING_CHECKPOINTS,
        sole_producer=WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION,
        reuse_scope="baseline fit parity",
        phase=InformationFlowPhase.HISTORICAL_CALIBRATION,
        partition_scheme=PartitionScheme.CHRONOLOGICAL,
        split_eligibility=(DatasetSplit.HISTORICAL,),
    ),
}


PRODUCER_OWNERSHIP_REGISTRY: dict[ArtifactBoundary, ProducerOwnership] = {
    **PREPROCESS_OWNED_BOUNDARIES,
    ArtifactBoundary.TRAINING_CHECKPOINTS: SHARED_PRODUCER_REGISTRY[
        SharedProducer.REPRESENTATION_DETECTOR_FIT
    ],
    ArtifactBoundary.SCORING_AND_SUMMARIES: SHARED_PRODUCER_REGISTRY[
        SharedProducer.ENCODING_SCORING_AND_SUMMARIES
    ],
    ArtifactBoundary.CALIBRATION_AND_CERTIFICATION: SHARED_PRODUCER_REGISTRY[
        SharedProducer.NESTED_PRE_CUTOFF_CALIBRATION
    ],
    ArtifactBoundary.EVALUATION: ProducerOwnership(
        boundary=ArtifactBoundary.EVALUATION,
        sole_producer=WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,
        reuse_scope="prospective-evaluation",
        phase=InformationFlowPhase.PROSPECTIVE_EVALUATION,
        partition_scheme=PartitionScheme.FEDERATED,
        split_eligibility=(DatasetSplit.PROSPECTIVE,),
    ),
    ArtifactBoundary.ANALYSIS: ProducerOwnership(
        boundary=ArtifactBoundary.ANALYSIS,
        sole_producer=WorkflowName.STATISTICAL_SYNTHESIS,
        reuse_scope="statistical-analysis",
        phase=InformationFlowPhase.PROSPECTIVE_EVALUATION,
        partition_scheme=PartitionScheme.CHRONOLOGICAL,
        split_eligibility=(DatasetSplit.PROSPECTIVE,),
    ),
    ArtifactBoundary.REPORTING: ProducerOwnership(
        boundary=ArtifactBoundary.REPORTING,
        sole_producer=WorkflowName.MANUSCRIPT_EVIDENCE_GENERATION,
        reuse_scope="manuscript-evidence",
        phase=InformationFlowPhase.PROSPECTIVE_EVALUATION,
        partition_scheme=PartitionScheme.CHRONOLOGICAL,
        split_eligibility=(DatasetSplit.HISTORICAL, DatasetSplit.PROSPECTIVE),
    ),
}


def is_preprocess_triggerable(key: SharedProducer | ArtifactBoundary) -> TriggerabilityFlag:
    if isinstance(key, SharedProducer):
        return key == SharedProducer.REPRESENTATION_DETECTOR_FIT
    return key in PREPROCESS_OWNED_BOUNDARIES


def ownership_for(key: SharedProducer | ArtifactBoundary) -> ProducerOwnership:
    if isinstance(key, SharedProducer):
        return SHARED_PRODUCER_REGISTRY[key]
    if key in PRODUCER_OWNERSHIP_REGISTRY:
        return PRODUCER_OWNERSHIP_REGISTRY[key]
    raise KeyError(f"No producer registered for {key}")


def registered_boundaries_for(workflow: WorkflowName) -> tuple[ArtifactBoundary, ...]:
    return tuple(b for b, p in PRODUCER_OWNERSHIP_REGISTRY.items() if p.sole_producer == workflow)


def resolve_reuse_or_recompute(
    existing_fingerprint: DependencyFingerprint | None,
    expected_fingerprint: DependencyFingerprint,
    overwrite_request: OverwriteRequest,
) -> ReuseDecision:
    if overwrite_request.requested:
        return ReuseDecision.OVERWRITE
    if existing_fingerprint is None or existing_fingerprint != expected_fingerprint:
        return ReuseDecision.STALE
    return ReuseDecision.REUSE
