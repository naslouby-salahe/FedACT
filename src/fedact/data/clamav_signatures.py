from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from fedact.domain.types import (
    ContentChecksum,
    SignatureAcquisitionTimestamp,
    SignatureSourceUrl,
    SupplementarySignatureArtifactName,
    SupplementarySignatureFileName,
    TimeoutSeconds,
)

SANESECURITY_MIRROR = SignatureSourceUrl("https://mirror.rollernet.us/sanesecurity")
_SANESECURITY_SUBDIRECTORY = Path("clamav-signatures") / "sanesecurity"
SUPPLEMENTARY_SIGNATURE_FILES = (
    SupplementarySignatureFileName.MALWARE_HASH,
    SupplementarySignatureFileName.ROGUE,
    SupplementarySignatureFileName.FOXHOLE_FILENAME,
    SupplementarySignatureFileName.FOXHOLE_GENERIC,
)


class ClamavSignatureAcquisitionError(RuntimeError):
    pass


@dataclass(frozen=True)
class SupplementarySignatureDigest:
    file_name: SupplementarySignatureFileName
    content_checksum: ContentChecksum


@dataclass(frozen=True)
class SupplementarySignatureManifest:
    directory: Path
    file_digests: tuple[SupplementarySignatureDigest, ...]
    fetched_at: SignatureAcquisitionTimestamp
    source: SignatureSourceUrl


def supplementary_signature_directory(raw_data_root: Path) -> Path:
    return raw_data_root / _SANESECURITY_SUBDIRECTORY


def _manifest_path(directory: Path) -> Path:
    return directory / SupplementarySignatureArtifactName.MANIFEST


def acquire_supplementary_signatures(
    raw_data_root: Path, transfer_deadline_seconds: TimeoutSeconds
) -> SupplementarySignatureManifest:
    directory = supplementary_signature_directory(raw_data_root)
    manifest_path = _manifest_path(directory)
    if manifest_path.is_file():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        return SupplementarySignatureManifest(
            directory=directory,
            file_digests=tuple(
                SupplementarySignatureDigest(
                    file_name=SupplementarySignatureFileName(entry["file_name"]),
                    content_checksum=ContentChecksum(entry["content_checksum"]),
                )
                for entry in payload["file_digests"]
            ),
            fetched_at=SignatureAcquisitionTimestamp(payload["fetched_at"]),
            source=SignatureSourceUrl(payload["source"]),
        )

    directory.mkdir(parents=True, exist_ok=True)
    file_digests: list[SupplementarySignatureDigest] = []
    for filename in SUPPLEMENTARY_SIGNATURE_FILES:
        url = f"{SANESECURITY_MIRROR}/{filename}"
        try:
            with urllib.request.urlopen(url, timeout=transfer_deadline_seconds) as response:
                payload_bytes = response.read()
        except urllib.error.URLError as error:
            raise ClamavSignatureAcquisitionError(f"failed to download {url}: {error}") from error
        destination = directory / filename
        temporary_destination = destination.with_suffix(destination.suffix + ".partial")
        temporary_destination.write_bytes(payload_bytes)
        temporary_destination.replace(destination)
        file_digests.append(
            SupplementarySignatureDigest(
                file_name=filename,
                content_checksum=ContentChecksum(
                    f"sha256:{hashlib.sha256(payload_bytes).hexdigest()}"
                ),
            )
        )

    manifest = SupplementarySignatureManifest(
        directory=directory,
        file_digests=tuple(file_digests),
        fetched_at=SignatureAcquisitionTimestamp(datetime.now(UTC).isoformat()),
        source=SANESECURITY_MIRROR,
    )
    manifest_path.write_text(
        json.dumps(
            {
                "file_digests": [
                    {
                        "file_name": digest.file_name,
                        "content_checksum": digest.content_checksum,
                    }
                    for digest in manifest.file_digests
                ],
                "fetched_at": manifest.fetched_at,
                "source": manifest.source,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest
