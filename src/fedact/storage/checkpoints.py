from __future__ import annotations

import os
from pathlib import Path

from fedact.domain.records import ContentChecksum, RawPayloadBytes, SourceText
from fedact.storage.metadata import content_checksum


class PayloadStorageError(ValueError):
    pass


def write_bytes_atomically(destination: Path, payload: RawPayloadBytes) -> ContentChecksum:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(f".{destination.name}.staging")
    staging.write_bytes(payload)
    os.replace(staging, destination)
    return content_checksum(payload)


def write_text_atomically(destination: Path, payload: SourceText) -> ContentChecksum:
    return write_bytes_atomically(destination, payload.encode("utf-8"))


def read_bytes(source: Path) -> RawPayloadBytes:
    if not source.is_file():
        raise PayloadStorageError(f"payload is missing: {source}")
    return source.read_bytes()
