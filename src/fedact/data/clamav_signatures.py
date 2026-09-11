from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

SANESECURITY_MIRROR = "https://mirror.rollernet.us/sanesecurity"
SUPPLEMENTARY_SIGNATURE_FILES = (
    "malwarehash.hsb",
    "rogue.hdb",
    "foxhole_filename.cdb",
    "foxhole_generic.cdb",
)


class ClamavSignatureAcquisitionError(RuntimeError):
    pass


@dataclass(frozen=True)
class SupplementarySignatureManifest:
    directory: Path
    file_sha256: dict[str, str]
    fetched_at: str
    source: str


def supplementary_signature_directory(raw_data_root: Path) -> Path:
    return raw_data_root / "clamav-signatures" / "sanesecurity"


def _manifest_path(directory: Path) -> Path:
    return directory / "manifest.json"


def acquire_supplementary_signatures(raw_data_root: Path) -> SupplementarySignatureManifest:
    directory = supplementary_signature_directory(raw_data_root)
    manifest_path = _manifest_path(directory)
    if manifest_path.is_file():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        return SupplementarySignatureManifest(
            directory=directory,
            file_sha256=payload["file_sha256"],
            fetched_at=payload["fetched_at"],
            source=payload["source"],
        )

    directory.mkdir(parents=True, exist_ok=True)
    file_sha256: dict[str, str] = {}
    for filename in SUPPLEMENTARY_SIGNATURE_FILES:
        url = f"{SANESECURITY_MIRROR}/{filename}"
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                payload_bytes = response.read()
        except urllib.error.URLError as error:
            raise ClamavSignatureAcquisitionError(f"failed to download {url}: {error}") from error
        destination = directory / filename
        temporary_destination = destination.with_suffix(destination.suffix + ".partial")
        temporary_destination.write_bytes(payload_bytes)
        temporary_destination.replace(destination)
        file_sha256[filename] = hashlib.sha256(payload_bytes).hexdigest()

    manifest = SupplementarySignatureManifest(
        directory=directory,
        file_sha256=file_sha256,
        fetched_at=datetime.now(UTC).isoformat(),
        source=SANESECURITY_MIRROR,
    )
    manifest_path.write_text(
        json.dumps(
            {
                "file_sha256": manifest.file_sha256,
                "fetched_at": manifest.fetched_at,
                "source": manifest.source,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return manifest
