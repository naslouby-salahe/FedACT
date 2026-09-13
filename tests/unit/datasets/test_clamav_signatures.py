from __future__ import annotations

import json
import urllib.error
from pathlib import Path
from types import TracebackType
from typing import Self

import pytest

from fedact.data.clamav_signatures import (
    SUPPLEMENTARY_SIGNATURE_FILES,
    ClamavSignatureAcquisitionError,
    SupplementarySignatureManifest,
    acquire_supplementary_signatures,
    supplementary_signature_directory,
)
from fedact.domain.types import (
    SupplementarySignatureArtifactName,
    SupplementarySignatureFileName,
    TimeoutSeconds,
)

TRANSFER_DEADLINE: TimeoutSeconds = 5.0


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_value: BaseException | None,
        _traceback: TracebackType | None,
    ) -> None:
        return None


class _SignatureMirrorOpener:
    def __init__(self) -> None:
        self.requested_urls: list[str] = []
        self.deadlines: list[float] = []

    def __call__(self, url: str, timeout: float) -> _FakeResponse:
        self.requested_urls.append(url)
        self.deadlines.append(timeout)
        return _FakeResponse(f"signature-body-for:{url}".encode())


class _ForbiddenOpener:
    def __call__(self, url: str, timeout: float) -> _FakeResponse:
        raise AssertionError(f"a cached manifest must not trigger a download (timeout={timeout})")


class _FailingOpener:
    def __init__(self) -> None:
        self.deadlines: list[float] = []

    def __call__(self, url: str, timeout: float) -> _FakeResponse:
        self.deadlines.append(timeout)
        raise urllib.error.URLError("mirror unreachable")


def test_signature_directory_lives_under_the_raw_root(tmp_path: Path) -> None:
    assert supplementary_signature_directory(tmp_path) == (
        tmp_path / "clamav-signatures" / "sanesecurity"
    )


def test_fresh_acquisition_downloads_every_supplementary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opener = _SignatureMirrorOpener()
    monkeypatch.setattr("fedact.data.clamav_signatures.urllib.request.urlopen", opener)
    manifest = acquire_supplementary_signatures(tmp_path, TRANSFER_DEADLINE)

    assert len(opener.requested_urls) == 4
    assert opener.deadlines == [TRANSFER_DEADLINE] * 4
    assert len(manifest.file_digests) == 4
    assert {digest.file_name for digest in manifest.file_digests} == set(
        SupplementarySignatureFileName
    )
    for digest in manifest.file_digests:
        assert digest.content_checksum.startswith("sha256:")
        assert (manifest.directory / digest.file_name).is_file()
    assert manifest.fetched_at
    assert manifest.source


def test_fresh_acquisition_persists_a_readable_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "fedact.data.clamav_signatures.urllib.request.urlopen", _SignatureMirrorOpener()
    )
    manifest = acquire_supplementary_signatures(tmp_path, TRANSFER_DEADLINE)
    manifest_path = manifest.directory / SupplementarySignatureArtifactName.MANIFEST
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert payload["source"] == manifest.source
    assert payload["fetched_at"] == manifest.fetched_at
    recorded = {
        SupplementarySignatureFileName(entry["file_name"]): entry["content_checksum"]
        for entry in payload["file_digests"]
    }
    assert recorded == {
        digest.file_name: digest.content_checksum for digest in manifest.file_digests
    }


def test_cached_manifest_is_reused_without_re_downloading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "fedact.data.clamav_signatures.urllib.request.urlopen", _SignatureMirrorOpener()
    )
    first = acquire_supplementary_signatures(tmp_path, TRANSFER_DEADLINE)

    monkeypatch.setattr("fedact.data.clamav_signatures.urllib.request.urlopen", _ForbiddenOpener())
    second = acquire_supplementary_signatures(tmp_path, TRANSFER_DEADLINE)
    assert second.file_digests == first.file_digests
    assert second.fetched_at == first.fetched_at
    assert isinstance(second, SupplementarySignatureManifest)


def test_mirror_failure_is_reported_as_an_acquisition_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    failing = _FailingOpener()
    monkeypatch.setattr("fedact.data.clamav_signatures.urllib.request.urlopen", failing)
    with pytest.raises(ClamavSignatureAcquisitionError, match="failed to download"):
        acquire_supplementary_signatures(tmp_path, TRANSFER_DEADLINE)
    assert failing.deadlines == [TRANSFER_DEADLINE]


def test_no_partial_files_survive_a_successful_acquisition(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "fedact.data.clamav_signatures.urllib.request.urlopen", _SignatureMirrorOpener()
    )
    manifest = acquire_supplementary_signatures(tmp_path, TRANSFER_DEADLINE)
    assert list(manifest.directory.glob("*.partial")) == []


def test_downloads_address_the_configured_mirror(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    opener = _SignatureMirrorOpener()
    monkeypatch.setattr("fedact.data.clamav_signatures.urllib.request.urlopen", opener)
    acquire_supplementary_signatures(tmp_path, TRANSFER_DEADLINE)
    assert all(url.startswith("https://") for url in opener.requested_urls)
    assert [url.rsplit("/", 1)[1] for url in opener.requested_urls] == [
        filename.value for filename in SUPPLEMENTARY_SIGNATURE_FILES
    ]
