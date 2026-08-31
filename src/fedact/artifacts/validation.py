from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from fedact.artifacts.identity import ContentChecksum
from fedact.artifacts.manifests import ArtifactManifest, ManifestContractError
from fedact.domain.enums import ArtifactLifecycleState
from fedact.domain.records import DependencyFingerprint


class ArtifactReuseError(ValueError):
    pass


def assert_complete_only_reuse(
    manifest: ArtifactManifest,
    expected_dependency_fingerprint: DependencyFingerprint,
) -> None:
    if manifest.state is not ArtifactLifecycleState.COMPLETE:
        raise ArtifactReuseError("artifact is not COMPLETE and may never be reused")
    if manifest.dependency_fingerprint != expected_dependency_fingerprint:
        raise ArtifactReuseError(
            "artifact dependency fingerprint does not match the currently expected fingerprint"
        )


def assert_manifest_integrity(
    manifest: ArtifactManifest, payload_checksum: ContentChecksum
) -> None:
    if manifest.content_checksum_or_checkpoint_hash != payload_checksum:
        raise ManifestContractError("manifest content checksum does not match stored payload")


def read_validated_json_model[ValidatedModel: BaseModel](
    source: Path, model_type: type[ValidatedModel]
) -> ValidatedModel:
    return model_type.model_validate_json(source.read_text(encoding="utf-8"))
