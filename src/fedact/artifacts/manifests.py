from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from fedact.artifacts.identity import (
    ArtifactIdentity,
    ContentChecksum,
    EnvironmentFingerprint,
    MaterialConfigurationHash,
    ProducerCodeFingerprint,
    ScientificKey,
)
from fedact.config.models import StrictModel
from fedact.domain.enums import (
    ArtifactLifecycleState,
    ExecutableWorkflowName,
    RequiredScientificArtifact,
    ScientificOutcome,
    WorkflowName,
)
from fedact.domain.records import (
    CommitHash,
    DegradationValue,
    DependencyFingerprint,
    MetricRate,
    ProducerIdentifier,
)


class ManifestContractError(ValueError):
    pass


@dataclass(frozen=True)
class ArtifactManifest:
    artifact_type: RequiredScientificArtifact
    artifact_identity: ArtifactIdentity
    producer: ProducerIdentifier
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
    created_by_repository_commit: CommitHash

    def __post_init__(self) -> None:
        if self.state is not ArtifactLifecycleState.COMPLETE:
            raise ManifestContractError(
                f"only COMPLETE artifacts may carry a reusable manifest; got {self.state}"
            )


class WorkflowResultRecord(StrictModel):
    workflow: ExecutableWorkflowName
    scientific_outcome: ScientificOutcome
    mean_false_negative_rate: MetricRate | None = None
    mean_certification_rate: MetricRate | None = None
    clean_fnr_degradation_percentage_points: DegradationValue | None = None


def workflow_result_path(experiment_directory: Path) -> Path:
    return experiment_directory / "result.json"


def write_workflow_result(experiment_directory: Path, record: WorkflowResultRecord) -> Path:
    from fedact.artifacts.storage import write_text_atomically

    destination = workflow_result_path(experiment_directory)
    from fedact.domain.records import SourceText

    write_text_atomically(destination, SourceText(record.model_dump_json(indent=2)))
    return destination


def read_workflow_result(experiment_directory: Path) -> WorkflowResultRecord | None:
    from fedact.artifacts.validation import read_validated_json_model

    source = workflow_result_path(experiment_directory)
    if not source.is_file():
        return None
    return read_validated_json_model(source, WorkflowResultRecord)
