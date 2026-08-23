from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import NewType

from fedact.domain.records import ContentChecksum, DependencyFingerprint

CanonicalPayload = NewType("CanonicalPayload", str)
HexDigest = NewType("HexDigest", str)
ProducerCodeFingerprint = NewType("ProducerCodeFingerprint", str)
EnvironmentFingerprint = NewType("EnvironmentFingerprint", str)
MaterialConfigurationHash = NewType("MaterialConfigurationHash", str)
ArtifactIdentity = NewType("ArtifactIdentity", str)
ScientificKey = NewType("ScientificKey", str)


def canonical_json(value: object) -> CanonicalPayload:
    return CanonicalPayload(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    )


def sha256_digest(payload: CanonicalPayload) -> HexDigest:
    return HexDigest(f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}")


def content_checksum(content: bytes) -> ContentChecksum:
    return ContentChecksum(f"sha256:{hashlib.sha256(content).hexdigest()}")


@dataclass(frozen=True)
class MaterialDependency:
    name: str
    canonical_value: str


def compute_dependency_fingerprint(
    dependencies: tuple[MaterialDependency, ...],
) -> DependencyFingerprint:
    ordered = sorted(dependencies, key=lambda dependency: dependency.name)
    names = [dependency.name for dependency in ordered]
    if len(set(names)) != len(names):
        raise ValueError("material dependencies contain duplicate names")
    payload = canonical_json([{"name": d.name, "value": d.canonical_value} for d in ordered])
    return DependencyFingerprint(sha256_digest(payload))


def material_configuration_hash(selected_values: Mapping[str, object]) -> MaterialConfigurationHash:
    return MaterialConfigurationHash(sha256_digest(canonical_json(selected_values)))


def producer_code_fingerprint(sources: tuple[tuple[str, str], ...]) -> ProducerCodeFingerprint:
    ordered = sorted(sources, key=lambda entry: entry[0])
    if not ordered:
        raise ValueError("producer code fingerprint requires at least one source module")
    payload = canonical_json([{"module": name, "source": source} for name, source in ordered])
    return ProducerCodeFingerprint(sha256_digest(payload))


def environment_fingerprint(recorded_versions: Mapping[str, str]) -> EnvironmentFingerprint:
    return EnvironmentFingerprint(
        sha256_digest(canonical_json(dict(sorted(recorded_versions.items()))))
    )
