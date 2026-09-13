from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, cast

import pytest

from fedact.certification.actions import (
    ValidityStatus,
    apk_dynamic_validity_of,
    apk_structural_validity_status,
    maliciousness_validity_of,
)
from fedact.data.lamda_apk_emulator import DynamicRunResult, EmulatorHandle
from fedact.domain.types import (
    AndroidDeviceSerial,
    AndroidPackageName,
    ApkFileBytes,
    EmulatorProcess,
    FileSuffix,
    MonkeyEventCount,
    ObservableEvent,
    SeedValue,
    SimilarityScore,
    TimeoutSeconds,
)

PACKAGE_NAME = AndroidPackageName("com.example.app")
SOURCE_PATH = Path("/tmp/source.apk")
TRANSFORMED_PATH = Path("/tmp/transformed.apk")
MONKEY_EVENTS: MonkeyEventCount = 25
MONKEY_SEED: SeedValue = 7
EXECUTION_TIMEOUT: TimeoutSeconds = 5.0
MINIMUM_JACCARD: SimilarityScore = 0.5
APK_SUFFIX = FileSuffix(".apk")
INFECTED_EXIT_CODE = 1
CLEAN_EXIT_CODE = 0
TOOL_FAILURE_EXIT_CODE = 2
BADGING_STDOUT = b"package: name='com.example.app' versionCode='1'\n"


class _SubprocessStub:
    def __init__(self, returncode: int = CLEAN_EXIT_CODE, stdout: bytes = b"") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.calls: list[list[str]] = []

    def __call__(self, args: list[Any], **_kwargs: Any) -> Any:
        self.calls.append([str(item) for item in args])
        return subprocess.CompletedProcess(
            args=self.calls[-1], returncode=self.returncode, stdout=self.stdout, stderr=b""
        )


class _SmokeStub:
    def __init__(self, result: DynamicRunResult) -> None:
        self._result = result

    def __call__(
        self, emulator: EmulatorHandle, apk_path: Path, *args: Any, **kwargs: Any
    ) -> DynamicRunResult:
        return self._result


class _FailingSubprocessStub:
    def __call__(self, args: list[Any], **_kwargs: Any) -> Any:
        raise subprocess.CalledProcessError(returncode=1, cmd=[str(item) for item in args])


def _emulator() -> EmulatorHandle:
    return EmulatorHandle(
        sdk_root=Path("/opt/android-sdk"),
        serial=AndroidDeviceSerial("emulator-5554"),
        adb_deadline_seconds=EXECUTION_TIMEOUT,
        process=cast("EmulatorProcess", None),
    )


def _run_result(
    launched: bool, crashed: bool, events: frozenset[ObservableEvent]
) -> DynamicRunResult:
    return DynamicRunResult(launched=launched, crashed_or_anr=crashed, observable_events=events)


def test_infected_source_and_transformation_are_both_reported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _SubprocessStub(returncode=INFECTED_EXIT_CODE)
    monkeypatch.setattr("fedact.certification.actions.subprocess.run", stub)
    validity = maliciousness_validity_of(b"source", b"transformed", APK_SUFFIX)
    assert validity.source_detected is True
    assert validity.transformed_detected is True
    assert len(stub.calls) == 2
    assert stub.calls[0][0] == "clamscan"


def test_clean_source_and_transformation_are_both_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "fedact.certification.actions.subprocess.run", _SubprocessStub(returncode=CLEAN_EXIT_CODE)
    )
    validity = maliciousness_validity_of(b"source", b"transformed", APK_SUFFIX)
    assert validity.source_detected is False
    assert validity.transformed_detected is False


def test_supplementary_signature_directory_is_passed_to_clamscan(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    stub = _SubprocessStub(returncode=CLEAN_EXIT_CODE)
    monkeypatch.setattr("fedact.certification.actions.subprocess.run", stub)
    maliciousness_validity_of(b"source", b"transformed", APK_SUFFIX, tmp_path)
    assert str(tmp_path) in stub.calls[0]
    assert "-d" in stub.calls[0]


def test_unexpected_clamscan_exit_is_raised_rather_than_treated_as_clean(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "fedact.certification.actions.subprocess.run",
        _SubprocessStub(returncode=TOOL_FAILURE_EXIT_CODE),
    )
    with pytest.raises(RuntimeError, match="clamscan failed"):
        maliciousness_validity_of(b"source", b"transformed", APK_SUFFIX)


def test_apk_structural_validity_is_invalid_when_no_parser_accepts_the_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("fedact.certification.actions.subprocess.run", _FailingSubprocessStub())
    assert apk_structural_validity_status(ApkFileBytes(b"not-an-apk")) is ValidityStatus.INVALID


def test_apk_structural_validity_records_secondary_parser_disagreement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    stub = _SubprocessStub(stdout=BADGING_STDOUT)
    monkeypatch.setattr("fedact.certification.actions.subprocess.run", stub)
    validity = apk_structural_validity_status(ApkFileBytes(b"not-an-apk"))
    assert validity is ValidityStatus.INVALID
    assert stub.calls[0][0] == "aapt2"


def test_dynamic_validity_accepts_a_launched_and_behaviorally_stable_pair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = frozenset({ObservableEvent("start:com.example.app/.MainActivity")})
    monkeypatch.setattr(
        "fedact.certification.actions.run_dynamic_smoke",
        _SmokeStub(_run_result(True, False, events)),
    )
    smoke, behavior = apk_dynamic_validity_of(
        _emulator(),
        SOURCE_PATH,
        TRANSFORMED_PATH,
        PACKAGE_NAME,
        MONKEY_EVENTS,
        MONKEY_SEED,
        EXECUTION_TIMEOUT,
        MINIMUM_JACCARD,
    )
    assert smoke.source_launched is True
    assert smoke.transformed_launched is True
    assert smoke.no_new_crash_or_anr is True
    assert behavior.both_event_sets_empty is False
    assert behavior.jaccard_similarity == 1.0


def test_dynamic_validity_flags_a_crash_introduced_by_the_transformation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events = frozenset({ObservableEvent("start:com.example.app/.MainActivity")})

    def _smoke(
        emulator: EmulatorHandle, apk_path: Path, *args: Any, **kwargs: Any
    ) -> DynamicRunResult:
        crashed = apk_path == TRANSFORMED_PATH
        return _run_result(not crashed, crashed, events)

    monkeypatch.setattr("fedact.certification.actions.run_dynamic_smoke", _smoke)
    smoke, _behavior = apk_dynamic_validity_of(
        _emulator(),
        SOURCE_PATH,
        TRANSFORMED_PATH,
        PACKAGE_NAME,
        MONKEY_EVENTS,
        MONKEY_SEED,
        EXECUTION_TIMEOUT,
        MINIMUM_JACCARD,
    )
    assert smoke.transformed_launched is False
    assert smoke.no_new_crash_or_anr is False


def test_dynamic_validity_marks_two_empty_event_sets_explicitly(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "fedact.certification.actions.run_dynamic_smoke",
        _SmokeStub(_run_result(True, False, frozenset())),
    )
    _smoke, behavior = apk_dynamic_validity_of(
        _emulator(),
        SOURCE_PATH,
        TRANSFORMED_PATH,
        PACKAGE_NAME,
        MONKEY_EVENTS,
        MONKEY_SEED,
        EXECUTION_TIMEOUT,
        MINIMUM_JACCARD,
    )
    assert behavior.both_event_sets_empty is True
    assert behavior.jaccard_similarity == 0.0
