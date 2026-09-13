from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from fedact.data.ember2024 import (
    EmberRawRecord,
    PeMutationError,
    UpxAction,
    apply_upx_action,
    windowed_malicious_features,
)
from fedact.data.splits import calendar_month
from fedact.domain.types import PeFileBytes, SampleIdentifier

BEFORE_WINDOW_MONTH = "2023-09"
AFTER_WINDOW_MONTH = "2023-12"
ENDPOINT_MONTH = calendar_month(6)
TRANSITION_INTERVAL_MONTHS = 3
FEATURE_DIMENSION = 2
UPX_PATH = "/usr/bin/upx"


class _WhichStub:
    def __init__(self, resolved: str | None = None) -> None:
        self.resolved = resolved
        self.names: list[str] = []

    def __call__(self, name: str, *_args: Any, **_kwargs: Any) -> str | None:
        self.names.append(name)
        return self.resolved


class _SubprocessStub:
    def __init__(self, returncode: int = 0, stderr: bytes = b"") -> None:
        self.returncode = returncode
        self.stderr = stderr
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str], **_kwargs: Any) -> Any:
        self.calls.append([str(item) for item in args])
        return subprocess.CompletedProcess(
            args=self.calls[-1], returncode=self.returncode, stdout=b"", stderr=self.stderr
        )


def _record(sample_id: str, year_month: str, *, malicious: bool) -> EmberRawRecord:
    return EmberRawRecord(
        sample_hash=SampleIdentifier(sample_id),
        year_month=year_month,
        label=malicious,
        family="berbew",
    )


def test_upx_invocation_requires_the_toolchain(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("fedact.data.ember2024.shutil.which", _WhichStub())
    with pytest.raises(PeMutationError, match="not available on PATH"):
        apply_upx_action(PeFileBytes(b"pe-bytes"), UpxAction.PACK)


def test_upx_pack_invokes_the_best_compression_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("fedact.data.ember2024.shutil.which", _WhichStub(UPX_PATH))
    stub = _SubprocessStub()
    monkeypatch.setattr("fedact.data.ember2024.subprocess.run", stub)
    mutated = apply_upx_action(PeFileBytes(b"pe-bytes"), UpxAction.PACK)
    assert stub.calls[0][0] == UPX_PATH
    assert stub.calls[0][1] == "--best"
    assert bytes(mutated) == b"pe-bytes"


def test_upx_unpack_invokes_the_decompression_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("fedact.data.ember2024.shutil.which", _WhichStub(UPX_PATH))
    stub = _SubprocessStub()
    monkeypatch.setattr("fedact.data.ember2024.subprocess.run", stub)
    apply_upx_action(PeFileBytes(b"pe-bytes"), UpxAction.UNPACK)
    assert stub.calls[0][1] == "-d"


def test_upx_failure_is_reported_with_its_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("fedact.data.ember2024.shutil.which", _WhichStub(UPX_PATH))
    monkeypatch.setattr(
        "fedact.data.ember2024.subprocess.run",
        _SubprocessStub(returncode=1, stderr=b"upx: not packed"),
    )
    with pytest.raises(PeMutationError, match="upx: not packed"):
        apply_upx_action(PeFileBytes(b"pe-bytes"), UpxAction.UNPACK)


def test_upx_leaves_no_temporary_file_behind(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("fedact.data.ember2024.shutil.which", _WhichStub(UPX_PATH))
    stub = _SubprocessStub()
    monkeypatch.setattr("fedact.data.ember2024.subprocess.run", stub)
    apply_upx_action(PeFileBytes(b"pe-bytes"), UpxAction.PACK)
    temporary_path = Path(stub.calls[0][-1])
    assert not temporary_path.exists()


def test_windowed_malicious_features_splits_on_the_transition_boundary() -> None:
    records = (
        _record("before-1", BEFORE_WINDOW_MONTH, malicious=True),
        _record("after-1", AFTER_WINDOW_MONTH, malicious=True),
        _record("benign-1", BEFORE_WINDOW_MONTH, malicious=False),
    )
    features = np.array([[1.0, 1.0], [2.0, 2.0], [9.0, 9.0]], dtype=np.float32)
    before, after = windowed_malicious_features(
        records, features, ENDPOINT_MONTH, TRANSITION_INTERVAL_MONTHS
    )
    assert before.shape == (1, FEATURE_DIMENSION)
    assert after.shape == (1, FEATURE_DIMENSION)
    assert np.allclose(before[0], np.array([1.0, 1.0]))
    assert np.allclose(after[0], np.array([2.0, 2.0]))


def test_windowed_malicious_features_ignores_benign_records_entirely() -> None:
    records = (
        _record("benign-1", BEFORE_WINDOW_MONTH, malicious=False),
        _record("benign-2", AFTER_WINDOW_MONTH, malicious=False),
    )
    features = np.array([[5.0, 5.0], [6.0, 6.0]], dtype=np.float32)
    before, after = windowed_malicious_features(
        records, features, ENDPOINT_MONTH, TRANSITION_INTERVAL_MONTHS
    )
    assert before.shape == (0, FEATURE_DIMENSION)
    assert after.shape == (0, FEATURE_DIMENSION)
