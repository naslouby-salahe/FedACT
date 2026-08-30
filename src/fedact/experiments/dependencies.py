from __future__ import annotations

from dataclasses import dataclass

from fedact.domain.enums import ArtifactBoundary, WorkflowName
from fedact.domain.records import (
    ArtifactBoundaryContract,
    BoundaryFingerprint,
    BoundaryFingerprints,
    DependencyFingerprint,
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
