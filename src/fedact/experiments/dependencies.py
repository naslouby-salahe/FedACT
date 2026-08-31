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
from fedact.domain.records import (
    ArtifactBoundaryContract,
    ArtifactName,
    BoundaryFingerprint,
    BoundaryFingerprints,
    DependencyFingerprint,
    EpochIndex,
    TriggerabilityFlag,
    WorkflowDescription,
)

WORKFLOW_ORDER: tuple[WorkflowName, ...] = (
    WorkflowName.SCIENTIFIC_AND_CONFIGURATION_AUTHORITY,
    WorkflowName.MATHEMATICAL_AND_NUMERICAL_VERIFICATION,
    WorkflowName.SYNTHETIC_GENERATOR_SMOKE_VALIDATION,
    WorkflowName.SYNTHETIC_THEORY_AND_GEOMETRY_VALIDATION,
    WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT,
    WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION,
    WorkflowName.NESTED_PRE_CUTOFF_CALIBRATION,
    WorkflowName.REAL_DATA_ACTION_CERTIFICATE_VALIDATION,
    WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,
    WorkflowName.NOVELTY_CRITICAL_ABLATIONS,
    WorkflowName.FEDERATION_AND_COMPLEMENTARITY_EVALUATION,
    WorkflowName.ROBUSTNESS_AND_FAILURE_BOUNDARY_EVALUATION,
    WorkflowName.CROSS_CORPUS_GENERALIZATION,
    WorkflowName.COMMUNICATION_LIMITED_CLIENT_SELECTION,
    WorkflowName.STATISTICAL_SYNTHESIS,
    WorkflowName.MANUSCRIPT_EVIDENCE_GENERATION,
)

_REAL_DATA_PREREQUISITES: tuple[WorkflowName, ...] = (
    WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT,
    WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION,
    WorkflowName.NESTED_PRE_CUTOFF_CALIBRATION,
)

_WORKFLOW_PREREQUISITES: dict[WorkflowName, tuple[WorkflowName, ...]] = {
    WorkflowName.SCIENTIFIC_AND_CONFIGURATION_AUTHORITY: (),
    WorkflowName.MATHEMATICAL_AND_NUMERICAL_VERIFICATION: (
        WorkflowName.SCIENTIFIC_AND_CONFIGURATION_AUTHORITY,
    ),
    WorkflowName.SYNTHETIC_GENERATOR_SMOKE_VALIDATION: (
        WorkflowName.MATHEMATICAL_AND_NUMERICAL_VERIFICATION,
    ),
    WorkflowName.SYNTHETIC_THEORY_AND_GEOMETRY_VALIDATION: (
        WorkflowName.SYNTHETIC_GENERATOR_SMOKE_VALIDATION,
    ),
    WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT: (
        WorkflowName.SYNTHETIC_THEORY_AND_GEOMETRY_VALIDATION,
    ),
    WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION: (
        WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT,
    ),
    WorkflowName.NESTED_PRE_CUTOFF_CALIBRATION: (
        WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION,
    ),
    WorkflowName.REAL_DATA_ACTION_CERTIFICATE_VALIDATION: _REAL_DATA_PREREQUISITES,
    WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION: _REAL_DATA_PREREQUISITES,
    WorkflowName.NOVELTY_CRITICAL_ABLATIONS: (WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,),
    WorkflowName.FEDERATION_AND_COMPLEMENTARITY_EVALUATION: (
        WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,
    ),
    WorkflowName.ROBUSTNESS_AND_FAILURE_BOUNDARY_EVALUATION: (
        WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,
    ),
    WorkflowName.CROSS_CORPUS_GENERALIZATION: (WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,),
    WorkflowName.COMMUNICATION_LIMITED_CLIENT_SELECTION: (
        WorkflowName.FEDERATION_AND_COMPLEMENTARITY_EVALUATION,
    ),
    WorkflowName.STATISTICAL_SYNTHESIS: (
        WorkflowName.NOVELTY_CRITICAL_ABLATIONS,
        WorkflowName.FEDERATION_AND_COMPLEMENTARITY_EVALUATION,
        WorkflowName.ROBUSTNESS_AND_FAILURE_BOUNDARY_EVALUATION,
        WorkflowName.CROSS_CORPUS_GENERALIZATION,
        WorkflowName.REAL_DATA_ACTION_CERTIFICATE_VALIDATION,
    ),
    WorkflowName.MANUSCRIPT_EVIDENCE_GENERATION: (WorkflowName.STATISTICAL_SYNTHESIS,),
}

WORKFLOW_PREREQUISITES: dict[WorkflowName, tuple[WorkflowName, ...]] = {
    name: _WORKFLOW_PREREQUISITES[name] for name in WORKFLOW_ORDER
}

_ARTIFACT_BOUNDARY_CONTRACTS: tuple[ArtifactBoundaryContract, ...] = (
    ArtifactBoundaryContract(
        boundary=ArtifactBoundary.INPUTS,
        reusable_artifacts="Raw-data identity/checksum, authoritative configuration subsets,"
        "operator source assets",
        consumers=(
            ArtifactBoundary.DATASET_PREPARATION,
            ArtifactBoundary.PREPROCESSING_AND_SPLITS,
            ArtifactBoundary.TRAINING_CHECKPOINTS,
            ArtifactBoundary.SCORING_AND_SUMMARIES,
            ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
            ArtifactBoundary.EVALUATION,
            ArtifactBoundary.ANALYSIS,
            ArtifactBoundary.REPORTING,
        ),
    ),
    ArtifactBoundaryContract(
        boundary=ArtifactBoundary.DATASET_PREPARATION,
        reusable_artifacts="Parsed normalized records, schema/data-quality manifest, source"
        "chronology fields",
        consumers=(
            ArtifactBoundary.PREPROCESSING_AND_SPLITS,
            ArtifactBoundary.TRAINING_CHECKPOINTS,
            ArtifactBoundary.SCORING_AND_SUMMARIES,
            ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
            ArtifactBoundary.EVALUATION,
        ),
    ),
    ArtifactBoundaryContract(
        boundary=ArtifactBoundary.PREPROCESSING_AND_SPLITS,
        reusable_artifacts=(
            "Cutoff manifests, train/validation/test splits, client/cohort manifests, "
            "fitted preprocessing transforms, eligible operator/sample indices"
        ),
        consumers=(
            ArtifactBoundary.TRAINING_CHECKPOINTS,
            ArtifactBoundary.SCORING_AND_SUMMARIES,
            ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
            ArtifactBoundary.EVALUATION,
        ),
    ),
    ArtifactBoundaryContract(
        boundary=ArtifactBoundary.TRAINING_CHECKPOINTS,
        reusable_artifacts=(
            "Cutoff-fixed representation checkpoint, base detector checkpoint, "
            "independently fitted baseline checkpoints"
        ),
        consumers=(
            ArtifactBoundary.SCORING_AND_SUMMARIES,
            ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
            ArtifactBoundary.EVALUATION,
        ),
    ),
    ArtifactBoundaryContract(
        boundary=ArtifactBoundary.SCORING_AND_SUMMARIES,
        reusable_artifacts=(
            "Encoded samples, detector scores/predictions, malicious/control transition summaries, "
            "nuisance bases/constraints, action displacements"
        ),
        consumers=(
            ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
            ArtifactBoundary.EVALUATION,
        ),
    ),
    ArtifactBoundaryContract(
        boundary=ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
        reusable_artifacts=(
            "Nested calibration result, temporal model/process-error set, historical/prospective"
            "feasible sets, "
            "action intervals, decisions, certificates/abstentions"
        ),
        consumers=(ArtifactBoundary.EVALUATION,),
    ),
    ArtifactBoundaryContract(
        boundary=ArtifactBoundary.EVALUATION,
        reusable_artifacts=(
            "Per-cutoff/per-seed metrics, exposure curves, comparator outcomes, diagnostics"
        ),
        consumers=(ArtifactBoundary.ANALYSIS,),
    ),
    ArtifactBoundaryContract(
        boundary=ArtifactBoundary.ANALYSIS,
        reusable_artifacts=(
            "Paired contrasts, bootstrap objects, tests, multiplicity results, sensitivity"
            "summaries, "
            "claim-state inputs"
        ),
        consumers=(ArtifactBoundary.REPORTING,),
    ),
    ArtifactBoundaryContract(
        boundary=ArtifactBoundary.REPORTING,
        reusable_artifacts=(
            "Figures, tables, presentation-formatted values, compact metrics/statistics evidence, "
            "reproducibility evidence, evidence index"
        ),
        consumers=(),
        manuscript_only=True,
    ),
)

ARTIFACT_BOUNDARY_CONTRACTS: dict[ArtifactBoundary, ArtifactBoundaryContract] = {
    contract.boundary: contract for contract in _ARTIFACT_BOUNDARY_CONTRACTS
}


def boundary_contract(boundary: ArtifactBoundary) -> ArtifactBoundaryContract:
    return ARTIFACT_BOUNDARY_CONTRACTS[boundary]


def validate_workflow_prerequisite_graph() -> None:
    position = {name: index for index, name in enumerate(WORKFLOW_ORDER)}
    if len(position) != len(WORKFLOW_ORDER):
        raise ValueError("workflow order contains duplicate workflows")
    for name, prerequisites in WORKFLOW_PREREQUISITES.items():
        for prerequisite in prerequisites:
            if position[prerequisite] >= position[name]:
                raise ValueError(f"prerequisite {prerequisite} does not precede {name}")


@dataclass(frozen=True)
class UpstreamReferenceRequest:
    consumer: WorkflowName
    boundary: ArtifactBoundary
    dependency_fingerprint: DependencyFingerprint


def resolve_shared_upstream_fingerprint(
    requests: tuple[UpstreamReferenceRequest, ...],
) -> BoundaryFingerprints:
    resolved: dict[ArtifactBoundary, DependencyFingerprint] = {}
    for request in requests:
        existing = resolved.get(request.boundary)
        if existing is None:
            resolved[request.boundary] = request.dependency_fingerprint
        elif existing != request.dependency_fingerprint:
            raise ValueError(
                f"conflicting dependency fingerprints for boundary {request.boundary}: "
                f"{existing} versus {request.dependency_fingerprint}"
            )
    return BoundaryFingerprints(
        entries=tuple(
            BoundaryFingerprint(boundary=boundary, dependency_fingerprint=fingerprint)
            for boundary, fingerprint in resolved.items()
        )
    )


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


_PREPROCESS_STAGE_DEFINITIONS: tuple[
    tuple[ArtifactName, ArtifactBoundary, WorkflowDescription], ...
] = (
    ("raw discovery/checksum", ArtifactBoundary.DATASET_PREPARATION, "raw-data-manifests"),
    ("normalized parsed preparation", ArtifactBoundary.DATASET_PREPARATION, "parsed-samples"),
    (
        "chronology/cutoff construction",
        ArtifactBoundary.PREPROCESSING_AND_SPLITS,
        "chronological-and-federated-splits",
    ),
    ("real-data audits", ArtifactBoundary.PREPROCESSING_AND_SPLITS, "audit-manifests"),
)
PREPROCESS_STAGE_FLOW: tuple[PreprocessStage, ...] = tuple(
    PreprocessStage(stage_order=index, name=name, boundary=boundary, scope=scope)
    for index, (name, boundary, scope) in enumerate(_PREPROCESS_STAGE_DEFINITIONS, start=1)
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
