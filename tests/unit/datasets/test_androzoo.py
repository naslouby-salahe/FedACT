from __future__ import annotations

import hashlib
import urllib.error
import urllib.request
from pathlib import Path
from types import TracebackType
from typing import Self

import pytest

from fedact.data.androzoo import (
    ANDROZOO_DOWNLOAD_URL,
    AndroZooAcquisitionError,
    AndroZooCredentialError,
    acquire_lamda_apk,
    acquire_lamda_apks_within_budget,
    acquired_lamda_apk_sample_ids,
    androzoo_api_key_from_environment,
    androzoo_apk_destination,
)
from fedact.domain.types import AndroZooApiKey, ByteBudget, SampleIdentifier, TimeoutSeconds

API_KEY = AndroZooApiKey("test-api-key")
DEADLINE: TimeoutSeconds = 5.0
STUB_STATUS = 200


def _sample_id_for(payload: bytes) -> SampleIdentifier:
    return SampleIdentifier(hashlib.sha256(payload).hexdigest())


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


class _StubOpener:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self.requested_urls: list[str] = []
        self.deadlines: list[float] = []

    def __call__(self, request: urllib.request.Request, timeout: float) -> _FakeResponse:
        self.requested_urls.append(request.full_url)
        self.deadlines.append(timeout)
        return _FakeResponse(self._payload)


class _FailingOpener:
    def __init__(self) -> None:
        self.deadlines: list[float] = []

    def __call__(self, request: urllib.request.Request, timeout: float) -> _FakeResponse:
        self.deadlines.append(timeout)
        raise urllib.error.URLError("connection refused")


class _ForbiddenOpener:
    def __call__(self, request: urllib.request.Request, timeout: float) -> _FakeResponse:
        raise AssertionError(f"cached acquisition must not touch the network (timeout={timeout})")


def _stub_download(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> _StubOpener:
    opener = _StubOpener(payload)
    monkeypatch.setattr("fedact.data.androzoo.urllib.request.urlopen", opener)
    return opener


def test_api_key_is_required_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANDROZOO_API_KEY", raising=False)
    with pytest.raises(AndroZooCredentialError):
        androzoo_api_key_from_environment()


def test_api_key_is_returned_as_a_domain_value(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANDROZOO_API_KEY", "secret")
    assert androzoo_api_key_from_environment() == "secret"


def test_destination_lives_under_the_lamda_androzoo_directory(tmp_path: Path) -> None:
    assert androzoo_apk_destination(tmp_path, SampleIdentifier("abc")) == (
        tmp_path / "LAMDA" / "AndroZoo" / "abc.apk"
    )


def test_cached_apk_is_reused_without_any_network_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = b"cached-apk"
    sample_id = _sample_id_for(payload)
    destination = androzoo_apk_destination(tmp_path, sample_id)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(payload)

    monkeypatch.setattr("fedact.data.androzoo.urllib.request.urlopen", _ForbiddenOpener())
    record = acquire_lamda_apk(sample_id, tmp_path, API_KEY, DEADLINE)
    assert record.already_present is True
    assert record.byte_size == len(payload)
    assert record.destination == destination


def test_cached_apk_with_mismatched_content_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sample_id = SampleIdentifier("a" * 64)
    destination = androzoo_apk_destination(tmp_path, sample_id)
    destination.parent.mkdir(parents=True)
    destination.write_bytes(b"not-the-requested-sample")
    monkeypatch.setattr("fedact.data.androzoo.urllib.request.urlopen", _StubOpener(b"unused"))
    with pytest.raises(AndroZooAcquisitionError, match="mismatched"):
        acquire_lamda_apk(sample_id, tmp_path, API_KEY, DEADLINE)


def test_download_writes_the_verified_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = b"fresh-apk-bytes"
    sample_id = _sample_id_for(payload)
    _stub_download(monkeypatch, payload)
    record = acquire_lamda_apk(sample_id, tmp_path, API_KEY, DEADLINE)
    assert record.already_present is False
    assert record.byte_size == len(payload)
    assert record.destination.read_bytes() == payload


def test_download_request_carries_the_api_key_and_sample_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payload = b"request-shape"
    sample_id = _sample_id_for(payload)
    opener = _stub_download(monkeypatch, payload)
    acquire_lamda_apk(sample_id, tmp_path, API_KEY, DEADLINE)
    assert opener.requested_urls[0].startswith(f"{ANDROZOO_DOWNLOAD_URL}?")
    assert f"sha256={sample_id}" in opener.requested_urls[0]
    assert "apikey=test-api-key" in opener.requested_urls[0]
    assert opener.deadlines == [DEADLINE]


def test_content_that_does_not_match_the_requested_digest_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _stub_download(monkeypatch, b"a-different-apk")
    with pytest.raises(AndroZooAcquisitionError, match="does not match"):
        acquire_lamda_apk(SampleIdentifier("b" * 64), tmp_path, API_KEY, DEADLINE)


def test_transport_failure_is_reported_as_an_acquisition_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    failing = _FailingOpener()
    monkeypatch.setattr("fedact.data.androzoo.urllib.request.urlopen", failing)
    with pytest.raises(AndroZooAcquisitionError, match="download failed"):
        acquire_lamda_apk(SampleIdentifier("c" * 64), tmp_path, API_KEY, DEADLINE)
    assert failing.deadlines == [DEADLINE]


def test_budget_stops_acquisition_once_new_bytes_reach_the_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    payloads = [b"first-apk-payload", b"second-apk-payload"]
    sample_ids = tuple(_sample_id_for(payload) for payload in payloads)
    served = iter(payloads)

    class _SequencedOpener:
        def __init__(self) -> None:
            self.deadlines: list[float] = []

        def __call__(self, request: urllib.request.Request, timeout: float) -> _FakeResponse:
            self.deadlines.append(timeout)
            return _FakeResponse(next(served))

    monkeypatch.setattr("fedact.data.androzoo.urllib.request.urlopen", _SequencedOpener())
    records = acquire_lamda_apks_within_budget(
        sample_ids, tmp_path, API_KEY, ByteBudget(len(payloads[0])), DEADLINE
    )
    assert len(records) == 1
    assert records[0].sample_id == sample_ids[0]


def test_cached_samples_do_not_consume_the_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cached_payload = b"already-on-disk"
    fresh_payload = b"needs-downloading"
    cached_id = _sample_id_for(cached_payload)
    fresh_id = _sample_id_for(fresh_payload)
    cached_destination = androzoo_apk_destination(tmp_path, cached_id)
    cached_destination.parent.mkdir(parents=True)
    cached_destination.write_bytes(cached_payload)
    _stub_download(monkeypatch, fresh_payload)

    records = acquire_lamda_apks_within_budget(
        (cached_id, fresh_id), tmp_path, API_KEY, ByteBudget(len(fresh_payload)), DEADLINE
    )
    assert [record.sample_id for record in records] == [cached_id, fresh_id]
    assert records[0].already_present is True
    assert records[1].already_present is False


def test_acquired_sample_ids_are_empty_without_a_directory(tmp_path: Path) -> None:
    assert acquired_lamda_apk_sample_ids(tmp_path) == frozenset()


def test_acquired_sample_ids_list_digest_verified_files(tmp_path: Path) -> None:
    payload = b"verified-apk"
    sample_id = _sample_id_for(payload)
    directory = tmp_path / "LAMDA" / "AndroZoo"
    directory.mkdir(parents=True)
    (directory / f"{sample_id}.apk").write_bytes(payload)
    assert acquired_lamda_apk_sample_ids(tmp_path) == frozenset({sample_id})


def test_acquired_sample_ids_fail_closed_on_a_corrupt_cached_apk(tmp_path: Path) -> None:
    directory = tmp_path / "LAMDA" / "AndroZoo"
    directory.mkdir(parents=True)
    (directory / "unverified.apk").write_bytes(b"whose-name-is-not-its-digest")
    with pytest.raises(AndroZooAcquisitionError, match="mismatched"):
        acquired_lamda_apk_sample_ids(tmp_path)
