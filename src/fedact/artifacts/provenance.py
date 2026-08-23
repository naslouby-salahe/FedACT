from __future__ import annotations

from dataclasses import dataclass

from fedact.artifacts.identity import (
    ArtifactIdentity,
    ContentChecksum,
    EnvironmentFingerprint,
    MaterialConfigurationHash,
    ProducerCodeFingerprint,
    ScientificKey,
)
from fedact.domain.enums import (
    ArtifactLifecycleState,
    RequiredScientificArtifact,
    ScientificOutcome,
    WorkflowName,
)
from fedact.domain.records import DependencyFingerprint


class ProvenanceContractError(ValueError):
    pass


@dataclass(frozen=True)
class RunProvenance:
    workflow_name: WorkflowName
    configuration_hash: str
    repository_commit: str
    dataset_identity: str | None = None
    raw_checksum: str | None = None
    preprocessing_identity: str | None = None
    split_and_cutoff: str | None = None
    client_cohort_definition: str | None = None
    horizon: str | None = None
    representation_checkpoint_hash: str | None = None
    detector_checkpoint_hash: str | None = None
    seed_streams: tuple[str, ...] = ()
    upstream_artifact_identities: tuple[ArtifactIdentity, ...] = ()
    operator_library_identity: str | None = None
    solver_outcome: str | None = None
    producer_code_fingerprint: ProducerCodeFingerprint | None = None
    environment_fingerprint: EnvironmentFingerprint | None = None
    scientific_outcome: ScientificOutcome | None = None
    run_result: str | None = None


@dataclass(frozen=True)
class ArtifactManifest:
    artifact_type: RequiredScientificArtifact
    artifact_identity: ArtifactIdentity
    producer: str
    owner_workflow: WorkflowName
    dependency_fingerprint: DependencyFingerprint
    material_configuration_hash: MaterialConfigurationHash
    producer_code_fingerprint: ProducerCodeFingerprint
    relevant_environment_fingerprint: EnvironmentFingerprint
    upstream_artifact_identities: tuple[ArtifactIdentity, ...]
    scientific_key: ScientificKey
    content_checksum_or_checkpoint_hash: ContentChecksum
    state: ArtifactLifecycleState
    completion_record_checksum: ContentChecksum
    created_by_repository_commit: str

    def __post_init__(self) -> None:
        if self.state is not ArtifactLifecycleState.COMPLETE:
            raise ProvenanceContractError(
                f"only COMPLETE artifacts may carry a reusable manifest; got {self.state}"
            )


def assert_reusable(
    manifest: ArtifactManifest,
    expected_dependency_fingerprint: DependencyFingerprint,
) -> None:
    if manifest.state is not ArtifactLifecycleState.COMPLETE:
        raise ProvenanceContractError("artifact is not COMPLETE and may never be reused")
    if manifest.dependency_fingerprint != expected_dependency_fingerprint:
        raise ProvenanceContractError(
            "artifact dependency fingerprint does not match the currently expected fingerprint"
        )
