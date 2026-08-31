from __future__ import annotations

import dataclasses

import pytest

from fedact.artifacts.identity import (
    ArtifactIdentity,
    ContentChecksum,
    DependencyFingerprint,
    EnvironmentFingerprint,
    MaterialConfigurationHash,
    ProducerCodeFingerprint,
    ScientificKey,
)
from fedact.artifacts.manifests import ArtifactManifest, ManifestContractError
from fedact.artifacts.provenance import RunProvenance
from fedact.artifacts.validation import ArtifactReuseError, assert_complete_only_reuse
from fedact.config.loading import ConfigurationHash
from fedact.domain.enums import (
    ArtifactLifecycleState,
    RequiredScientificArtifact,
    ScientificOutcome,
    WorkflowName,
)
from fedact.domain.records import (
    CohortDefinition,
    DatasetIdentity,
    OperatorLibraryIdentity,
    PreprocessingIdentity,
    RepositoryCommit,
    RunResultSummary,
    SolverOutcomeRecord,
    SplitCutoffIdentity,
)


def manifest(state: ArtifactLifecycleState = ArtifactLifecycleState.COMPLETE) -> ArtifactManifest:
    return ArtifactManifest(
        artifact_type=RequiredScientificArtifact.NESTED_CALIBRATION_RESULTS,
        artifact_identity=ArtifactIdentity("sha256:" + "1" * 64),
        producer="fedact.calibration.nested",
        owner_workflow=WorkflowName.NESTED_PRE_CUTOFF_CALIBRATION,
        dependency_fingerprint=DependencyFingerprint("sha256:" + "2" * 64),
        material_configuration_hash=MaterialConfigurationHash("sha256:" + "3" * 64),
        producer_code_fingerprint=ProducerCodeFingerprint("sha256:" + "4" * 64),
        relevant_environment_fingerprint=EnvironmentFingerprint("sha256:" + "5" * 64),
        upstream_artifact_identities=(ArtifactIdentity("sha256:" + "6" * 64),),
        scientific_key=ScientificKey("calibration:primary"),
        content_checksum_or_checkpoint_hash=ContentChecksum("sha256:" + "7" * 64),
        state=state,
        completion_record_checksum=ContentChecksum("sha256:" + "8" * 64),
        created_by_repository_commit="05b83be",
    )


REQUIRED_MANIFEST_FIELDS: tuple[str, ...] = tuple(
    field.name for field in dataclasses.fields(ArtifactManifest)
)


def test_manifest_schema_contains_every_required_field() -> None:
    assert REQUIRED_MANIFEST_FIELDS == (
        "artifact_type",
        "artifact_identity",
        "producer",
        "owner_workflow",
        "dependency_fingerprint",
        "material_configuration_hash",
        "producer_code_fingerprint",
        "relevant_environment_fingerprint",
        "upstream_artifact_identities",
        "scientific_key",
        "content_checksum_or_checkpoint_hash",
        "state",
        "completion_record_checksum",
        "created_by_repository_commit",
    )


def test_manifest_state_must_be_complete() -> None:
    with pytest.raises(ManifestContractError):
        manifest(state=ArtifactLifecycleState.STAGING)
    with pytest.raises(ManifestContractError):
        manifest(state=ArtifactLifecycleState.INCOMPLETE)


def test_matching_fingerprint_allows_reuse() -> None:
    complete = manifest()
    assert_complete_only_reuse(complete, complete.dependency_fingerprint)


def test_fingerprint_mismatch_blocks_reuse() -> None:
    m = manifest()
    target_fp = DependencyFingerprint("sha256:" + "9" * 64)
    with pytest.raises(ArtifactReuseError, match="fingerprint"):
        assert_complete_only_reuse(m, target_fp)


def test_run_provenance_supports_every_reconstruction_item() -> None:
    provenance = RunProvenance(
        workflow_name=WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,
        configuration_hash=ConfigurationHash("sha256:2033b396"),
        repository_commit=RepositoryCommit("1cf8b45"),
        dataset_identity=DatasetIdentity("ember2024:win32_pe"),
        raw_checksum=ContentChecksum("sha256:" + "a" * 64),
        preprocessing_identity=PreprocessingIdentity("sha256:" + "b" * 64),
        split_and_cutoff_identity=SplitCutoffIdentity("cutoff:2024-03;window:12"),
        client_cohort_definition=CohortDefinition("client:cohort-a"),
        horizon_months=3,
        representation_checkpoint_hash=ContentChecksum("sha256:" + "c" * 64),
        detector_checkpoint_hash=ContentChecksum("sha256:" + "d" * 64),
        seed_streams=("detector_training:2001",),
        upstream_artifact_identities=(ArtifactIdentity("sha256:" + "e" * 64),),
        operator_library_identity=OperatorLibraryIdentity("sha256:" + "f" * 64),
        solver_outcome=SolverOutcomeRecord("optimal"),
        producer_code_fingerprint=ProducerCodeFingerprint("sha256:" + "0" * 64),
        environment_fingerprint=EnvironmentFingerprint("sha256:" + "1" * 63 + "0"),
        scientific_outcome=ScientificOutcome.PASS,
        run_result=RunResultSummary("completed"),
    )
    reconstructed = dataclasses.replace(provenance)
    assert reconstructed == provenance
    assert provenance.workflow_name is WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION
