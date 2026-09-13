from __future__ import annotations

import hashlib
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from fedact.domain.types import (
    AndroZooApiKey,
    ByteBudget,
    ByteCount,
    DataAvailabilityFlag,
    SampleIdentifier,
    TimeoutSeconds,
)

ANDROZOO_DOWNLOAD_URL = "https://androzoo.uni.lu/api/download"
ANDROZOO_API_KEY_ENVIRONMENT_VARIABLE = "ANDROZOO_API_KEY"

_ANDROZOO_APK_SUBDIRECTORY = Path("LAMDA") / "AndroZoo"


class AndroZooCredentialError(RuntimeError):
    pass


class AndroZooAcquisitionError(RuntimeError):
    pass


def androzoo_api_key_from_environment() -> AndroZooApiKey:
    key = os.environ.get(ANDROZOO_API_KEY_ENVIRONMENT_VARIABLE)
    if not key:
        raise AndroZooCredentialError(
            f"{ANDROZOO_API_KEY_ENVIRONMENT_VARIABLE} is not set in the environment"
        )
    return AndroZooApiKey(key)


@dataclass(frozen=True)
class AndroZooAcquisitionRecord:
    sample_id: SampleIdentifier
    destination: Path
    byte_size: ByteCount
    already_present: DataAvailabilityFlag


def androzoo_apk_destination(raw_data_root: Path, sample_id: SampleIdentifier) -> Path:
    return raw_data_root / _ANDROZOO_APK_SUBDIRECTORY / f"{sample_id}.apk"


def _verified_local_apk(
    destination: Path, sample_id: SampleIdentifier
) -> AndroZooAcquisitionRecord | None:
    if not destination.is_file():
        return None
    observed_hash = hashlib.sha256(destination.read_bytes()).hexdigest()
    if observed_hash != sample_id:
        raise AndroZooAcquisitionError(
            f"cached AndroZoo acquisition for {sample_id} has mismatched "
            f"sha256={observed_hash}; remove {destination} and re-acquire"
        )
    return AndroZooAcquisitionRecord(
        sample_id,
        destination,
        ByteCount(destination.stat().st_size),
        True,
    )


def acquire_lamda_apk(
    sample_id: SampleIdentifier,
    raw_data_root: Path,
    api_key: AndroZooApiKey,
    timeout_seconds: TimeoutSeconds,
) -> AndroZooAcquisitionRecord:
    destination = androzoo_apk_destination(raw_data_root, sample_id)
    cached = _verified_local_apk(destination, sample_id)
    if cached is not None:
        return cached

    query = urllib.parse.urlencode({"apikey": api_key, "sha256": sample_id})
    request = urllib.request.Request(f"{ANDROZOO_DOWNLOAD_URL}?{query}")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            payload = response.read()
    except urllib.error.URLError as error:
        raise AndroZooAcquisitionError(
            f"AndroZoo download failed for {sample_id}: {error}"
        ) from error

    observed_hash = hashlib.sha256(payload).hexdigest()
    if observed_hash != sample_id:
        raise AndroZooAcquisitionError(
            f"AndroZoo returned content whose sha256={observed_hash} does not match "
            f"the requested sample_id={sample_id}"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary_destination = destination.with_suffix(".apk.partial")
    temporary_destination.write_bytes(payload)
    temporary_destination.replace(destination)
    return AndroZooAcquisitionRecord(
        sample_id,
        destination,
        ByteCount(len(payload)),
        False,
    )


def acquire_lamda_apks_within_budget(
    sample_ids: tuple[SampleIdentifier, ...],
    raw_data_root: Path,
    api_key: AndroZooApiKey,
    max_total_bytes: ByteBudget,
    timeout_seconds: TimeoutSeconds,
) -> tuple[AndroZooAcquisitionRecord, ...]:
    acquired: list[AndroZooAcquisitionRecord] = []
    total_new_bytes = ByteCount(0)
    for sample_id in sample_ids:
        destination = androzoo_apk_destination(raw_data_root, sample_id)
        cached = _verified_local_apk(destination, sample_id)
        if cached is not None:
            acquired.append(cached)
            continue
        if total_new_bytes >= max_total_bytes:
            break
        record = acquire_lamda_apk(sample_id, raw_data_root, api_key, timeout_seconds)
        acquired.append(record)
        total_new_bytes += record.byte_size
    return tuple(acquired)


def acquired_lamda_apk_sample_ids(raw_data_root: Path) -> frozenset[SampleIdentifier]:
    directory = raw_data_root / _ANDROZOO_APK_SUBDIRECTORY
    if not directory.is_dir():
        return frozenset()
    verified: set[SampleIdentifier] = set()
    for candidate in directory.glob("*.apk"):
        sample_id = SampleIdentifier(candidate.stem)
        if _verified_local_apk(candidate, sample_id) is not None:
            verified.add(sample_id)
    return frozenset(verified)
