from __future__ import annotations

import os
from pathlib import Path

from fedact.artifacts.identity import ContentChecksum, content_checksum
from fedact.domain.records import RawPayloadBytes, SourceText


class ArtifactStorageError(ValueError):
    pass


def write_bytes_atomically(destination: Path, payload: RawPayloadBytes) -> ContentChecksum:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(f".{destination.name}.staging")
    staging.write_bytes(payload)
    os.replace(staging, destination)
    return content_checksum(payload)


def write_text_atomically(destination: Path, payload: SourceText) -> ContentChecksum:
    return write_bytes_atomically(destination, RawPayloadBytes(payload.encode("utf-8")))


def read_bytes(source: Path) -> RawPayloadBytes:
    if not source.is_file():
        raise ArtifactStorageError(f"artifact payload is missing: {source}")
    return RawPayloadBytes(source.read_bytes())
