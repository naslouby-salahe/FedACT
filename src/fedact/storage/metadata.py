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
    ParameterName,
    RawPayloadBytes,
)

DeterministicJsonPayload = NewType("DeterministicJsonPayload", str)
HexDigest = NewType("HexDigest", str)
ArtifactIdentity = NewType("ArtifactIdentity", str)


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
