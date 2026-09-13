from __future__ import annotations

import hashlib
import shutil
import urllib.request
from pathlib import Path
from types import TracebackType
from typing import Self

import pandas as pd
import pytest

from fedact.domain.types import ByteBudget, SampleIdentifier
from fedact.workflow import (
    AcquisitionRequestError,
    discover_repository_root,
    run_acquire,
)

BUDGET = ByteBudget(1024)
API_KEY_ENVIRONMENT_VARIABLE = "ANDROZOO_API_KEY"
MALICIOUS_VT_COUNT = 8
BENIGN_VT_COUNT = 0
FEATURE_COLUMN_COUNT = 3


def _sample_payload(index: int) -> bytes:
    return f"androzoo-apk-payload-{index}".encode()


def _sample_identity(index: int) -> SampleIdentifier:
    return SampleIdentifier(hashlib.sha256(_sample_payload(index)).hexdigest())


def _release_rows(index: int, year_month: str, family: str, malicious: bool) -> dict[str, object]:
    row: dict[str, object] = {
        "hash": _sample_identity(index),
        "year_month": year_month,
        "label": malicious,
        "vt_count": MALICIOUS_VT_COUNT if malicious else BENIGN_VT_COUNT,
        "family": family,
    }
    for column in range(FEATURE_COLUMN_COUNT):
        row[f"feat_{column}"] = float((index + column) % 7) / 7.0
    return row


def _write_release(
    repository_root: Path, rows: list[dict[str, object]], relative_directory: str
) -> Path:
    release = repository_root / relative_directory
    release.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(release / "lamda_baseline.parquet", index=False)
    return release


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


class _PayloadOpener:
    def __init__(self) -> None:
        self.deadlines: list[float] = []

    def __call__(self, request: urllib.request.Request, timeout: float) -> _FakeResponse:
        self.deadlines.append(timeout)
        digest = request.full_url.rsplit("sha256=", 1)[-1]
        index = next(
            candidate
            for candidate in range(16)
            if hashlib.sha256(_sample_payload(candidate)).hexdigest() == digest
        )
        return _FakeResponse(_sample_payload(index))


@pytest.fixture
def temporary_repository(tmp_path: Path, repository_root: Path) -> Path:
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "fedact"\n', encoding="utf-8")
    configuration_directory = tmp_path / "configs"
    configuration_directory.mkdir()
    shutil.copy(
        repository_root / "configs" / "fedact.yaml",
        configuration_directory / "fedact.yaml",
    )
    return tmp_path


def test_repository_root_is_discovered_from_its_configuration(temporary_repository: Path) -> None:
    nested = temporary_repository / "outputs" / "experiments"
    nested.mkdir(parents=True)
    assert discover_repository_root(nested) == temporary_repository


def test_repository_root_discovery_fails_closed_outside_a_repository(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="repository root not found"):
        discover_repository_root(tmp_path)


def test_acquire_requires_the_lamda_release_directory(temporary_repository: Path) -> None:
    with pytest.raises(AcquisitionRequestError, match="LAMDA release directory is missing"):
        run_acquire(BUDGET, temporary_repository)


def test_acquire_requires_an_identifiable_dominant_cohort(temporary_repository: Path) -> None:
    (temporary_repository / "data" / "raw" / "LAMDA" / "Baseline").mkdir(parents=True)
    with pytest.raises(AcquisitionRequestError, match="no dominant malicious family cohort"):
        run_acquire(BUDGET, temporary_repository)


def test_acquire_downloads_the_outstanding_dominant_cohort_samples(
    temporary_repository: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_release(
        temporary_repository,
        [
            _release_rows(0, "2023-01", "berbew", malicious=True),
            _release_rows(1, "2023-02", "berbew", malicious=True),
            _release_rows(2, "2023-03", "drixed", malicious=True),
            _release_rows(3, "2023-03", "berbew", malicious=False),
        ],
        "data/raw/LAMDA/Baseline",
    )
    monkeypatch.setenv(API_KEY_ENVIRONMENT_VARIABLE, "test-api-key")
    opener = _PayloadOpener()
    monkeypatch.setattr("fedact.data.androzoo.urllib.request.urlopen", opener)

    run_acquire(BUDGET, temporary_repository)

    acquired_directory = temporary_repository / "data" / "raw" / "LAMDA" / "AndroZoo"
    downloaded = {path.name for path in acquired_directory.glob("*.apk")}
    assert downloaded == {
        f"{_sample_identity(0)}.apk",
        f"{_sample_identity(1)}.apk",
    }
    output = capsys.readouterr().out
    assert "cohort=berbew" in output
    assert "outstanding=2" in output
    assert "acquired=2" in output


def test_acquire_reports_when_the_dominant_cohort_has_nothing_outstanding(
    temporary_repository: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _write_release(
        temporary_repository,
        [_release_rows(0, "2023-01", "berbew", malicious=True)],
        "data/raw/LAMDA/Baseline",
    )
    cached_directory = temporary_repository / "data" / "raw" / "LAMDA" / "AndroZoo"
    cached_directory.mkdir(parents=True)
    (cached_directory / f"{_sample_identity(0)}.apk").write_bytes(_sample_payload(0))
    monkeypatch.setenv(API_KEY_ENVIRONMENT_VARIABLE, "test-api-key")

    def _forbidden(request: object, timeout: float) -> object:
        raise AssertionError("nothing outstanding means no download")

    monkeypatch.setattr("fedact.data.androzoo.urllib.request.urlopen", _forbidden)

    run_acquire(BUDGET, temporary_repository)
    assert "no outstanding samples" in capsys.readouterr().out
