from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import NewType

from fedact.domain.records import (
    ContentChecksum,
    DependencyFingerprint,
    HashDigest,
    JsonEncodableValue,
    ModuleQualifiedName,
    ParameterName,
    RawPayloadBytes,
    SourceText,
    ToolchainIdentifier,
    VersionText,
)

DeterministicJsonPayload = NewType("DeterministicJsonPayload", str)
HexDigest = NewType("HexDigest", str)
ProducerCodeFingerprint = NewType("ProducerCodeFingerprint", str)
EnvironmentFingerprint = NewType("EnvironmentFingerprint", str)
MaterialConfigurationHash = NewType("MaterialConfigurationHash", str)
ArtifactIdentity = NewType("ArtifactIdentity", str)
ScientificKey = NewType("ScientificKey", str)


def deterministic_json(value: JsonEncodableValue) -> DeterministicJsonPayload:
    return DeterministicJsonPayload(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    )


def sha256_digest(payload: DeterministicJsonPayload) -> HexDigest:
    return HexDigest(f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}")


def content_checksum(content: RawPayloadBytes) -> ContentChecksum:
    return ContentChecksum(f"sha256:{hashlib.sha256(content).hexdigest()}")


@dataclass(frozen=True)
class MaterialDependency:
    name: ParameterName
    content_hash: HashDigest


def compute_dependency_fingerprint(
    dependencies: tuple[MaterialDependency, ...],
) -> DependencyFingerprint:
    ordered = sorted(dependencies, key=lambda dependency: dependency.name)
    names = [dependency.name for dependency in ordered]
    if len(set(names)) != len(names):
        raise ValueError("material dependencies contain duplicate names")
    payload = deterministic_json([{"name": d.name, "value": d.content_hash} for d in ordered])
    return DependencyFingerprint(sha256_digest(payload))


@dataclass(frozen=True)
class SelectedConfigurationValue:
    name: ParameterName
    value: JsonEncodableValue


def material_configuration_hash(
    selected_values: tuple[SelectedConfigurationValue, ...],
) -> MaterialConfigurationHash:
    ordered = sorted(selected_values, key=lambda selected: selected.name)
    payload = deterministic_json([{"name": s.name, "value": s.value} for s in ordered])
    return MaterialConfigurationHash(sha256_digest(payload))


@dataclass(frozen=True)
class ProducerSourceModule:
    module: ModuleQualifiedName
    source: SourceText


def producer_code_fingerprint(
    sources: tuple[ProducerSourceModule, ...],
) -> ProducerCodeFingerprint:
    ordered = sorted(sources, key=lambda entry: entry.module)
    if not ordered:
        raise ValueError("producer code fingerprint requires at least one source module")
    payload = deterministic_json(
        [{"module": entry.module, "source": entry.source} for entry in ordered]
    )
    return ProducerCodeFingerprint(sha256_digest(payload))


@dataclass(frozen=True)
class RuntimeComponentVersion:
    component: ToolchainIdentifier
    version: VersionText


def environment_fingerprint(
    recorded_versions: tuple[RuntimeComponentVersion, ...],
) -> EnvironmentFingerprint:
    ordered = sorted(recorded_versions, key=lambda entry: entry.component)
    payload = deterministic_json(
        [{"component": entry.component, "version": entry.version} for entry in ordered]
    )
    return EnvironmentFingerprint(sha256_digest(payload))
