from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, cast

import pytest

from fedact.data.lamda_apk_emulator import (
    AndroidEmulatorError,
    EmulatorHandle,
    android_sdk_root_from_environment,
    boot_emulator,
    ensure_avd,
    jaccard_similarity,
    run_dynamic_smoke,
    shutdown_emulator,
)
from fedact.domain.types import (
    AndroidAvdName,
    AndroidDeviceSerial,
    AndroidPackageName,
    AndroidSystemImage,
    EmulatorPort,
    EmulatorProcess,
    ObservableEvent,
    TimeoutSeconds,
)

SDK_ROOT = Path("/opt/android-sdk")
AVD_NAME = AndroidAvdName("fedact-operator-validation")
SYSTEM_IMAGE = AndroidSystemImage("system-images;android-30;google_apis;x86_64")
PACKAGE_NAME = AndroidPackageName("com.example.app")
SERIAL = AndroidDeviceSerial("emulator-5554")
BOOT_TIMEOUT: TimeoutSeconds = 30.0
EMULATOR_PORT: EmulatorPort = 5554
POLL_INTERVAL_SECONDS = 5.0
SHUTDOWN_TIMEOUT_SECONDS = 30.0
ADB_DEADLINE: TimeoutSeconds = 30.0
JAVA_HOME = Path("/usr/lib/jvm/java-17-openjdk-amd64")

CLEAN_LOGCAT = (
    b"START u0 {cmp=com.example.app/.MainActivity}\nDisplayed com.example.app/.MainActivity\n"
)
CRASH_LOGCAT = b"FATAL EXCEPTION: main\n"


def _completed(stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0) -> Any:
    return subprocess.CompletedProcess(
        args=["adb"], returncode=returncode, stdout=stdout, stderr=stderr
    )


class _RunRecorder:
    def __init__(self, responses: list[Any] | None = None) -> None:
        self.responses = list(responses or [])
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str], **_kwargs: Any) -> Any:
        self.calls.append([str(item) for item in args])
        if self.responses:
            response = self.responses.pop(0)
            if isinstance(response, BaseException):
                raise response
            return response
        return _completed()


class _FakeProcess:
    def __init__(self, wait_expires: bool = False) -> None:
        self.terminated = False
        self.killed = False
        self.waited_with: float | None = None
        self._wait_expires = wait_expires

    def terminate(self) -> None:
        self.terminated = True

    def kill(self) -> None:
        self.killed = True

    def wait(self, timeout: float | None = None) -> int:
        self.waited_with = timeout
        if self._wait_expires:
            raise subprocess.TimeoutExpired(cmd="emulator", timeout=timeout or 0.0)
        return 0


class _PopenStub:
    def __init__(self, process: _FakeProcess) -> None:
        self._process = process

    def __call__(self, args: list[str], **_kwargs: Any) -> subprocess.Popen[bytes]:
        return cast("subprocess.Popen[bytes]", self._process)


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> _Clock:
    fake = _Clock()
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.time.monotonic", fake.monotonic)
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.time.sleep", fake.sleep)
    return fake


def _handle(process: _FakeProcess | None = None) -> EmulatorHandle:
    return EmulatorHandle(
        sdk_root=SDK_ROOT,
        serial=SERIAL,
        adb_deadline_seconds=ADB_DEADLINE,
        process=cast("EmulatorProcess", process or _FakeProcess()),
    )


def test_sdk_root_comes_from_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANDROID_SDK_ROOT", "/opt/android-sdk")
    assert android_sdk_root_from_environment() == SDK_ROOT


def test_missing_sdk_root_is_reported_explicitly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANDROID_SDK_ROOT", raising=False)
    with pytest.raises(AndroidEmulatorError, match="not set"):
        android_sdk_root_from_environment()


def test_ensure_avd_is_a_no_op_when_the_avd_already_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorder = _RunRecorder(
        [_completed(stdout=b"Available Android Virtual Devices:\n  fedact-operator-validation")]
    )
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.subprocess.run", recorder)
    ensure_avd(SDK_ROOT, AVD_NAME, SYSTEM_IMAGE, JAVA_HOME)
    assert len(recorder.calls) == 1
    assert recorder.calls[0][:3] == [
        str(SDK_ROOT / "cmdline-tools/latest/bin/avdmanager"),
        "list",
        "avd",
    ]


def test_ensure_avd_creates_the_avd_with_the_configured_system_image(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorder = _RunRecorder([_completed(stdout=b"no avds"), _completed()])
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.subprocess.run", recorder)
    ensure_avd(SDK_ROOT, AVD_NAME, SYSTEM_IMAGE, JAVA_HOME)
    create_call = recorder.calls[1]
    assert create_call[1:3] == ["create", "avd"]
    assert AVD_NAME in create_call
    assert SYSTEM_IMAGE in create_call


def test_ensure_avd_failure_surfaces_the_tool_stderr(monkeypatch: pytest.MonkeyPatch) -> None:
    recorder = _RunRecorder(
        [_completed(stdout=b"no avds"), _completed(stderr=b"package not installed", returncode=1)]
    )
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.subprocess.run", recorder)
    with pytest.raises(AndroidEmulatorError, match="package not installed"):
        ensure_avd(SDK_ROOT, AVD_NAME, SYSTEM_IMAGE, JAVA_HOME)


def test_boot_emulator_returns_a_handle_once_boot_completes(
    monkeypatch: pytest.MonkeyPatch, clock: _Clock
) -> None:
    process = _FakeProcess()
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.subprocess.Popen", _PopenStub(process))
    recorder = _RunRecorder([_completed(stdout=b"0"), _completed(stdout=b"1")])
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.subprocess.run", recorder)

    handle = boot_emulator(SDK_ROOT, AVD_NAME, EMULATOR_PORT, BOOT_TIMEOUT, ADB_DEADLINE)
    assert handle.serial == SERIAL
    assert handle.adb_deadline_seconds == ADB_DEADLINE
    assert len(recorder.calls) == 2
    assert recorder.calls[0][-3:] == ["shell", "getprop", "sys.boot_completed"]
    assert clock.now == POLL_INTERVAL_SECONDS


def test_boot_emulator_terminates_the_process_when_boot_times_out(
    monkeypatch: pytest.MonkeyPatch, clock: _Clock
) -> None:
    process = _FakeProcess()
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.subprocess.Popen", _PopenStub(process))
    monkeypatch.setattr(
        "fedact.data.lamda_apk_emulator.subprocess.run",
        _RunRecorder([_completed(stdout=b"0")] * 20),
    )
    with pytest.raises(AndroidEmulatorError, match="did not boot"):
        boot_emulator(SDK_ROOT, AVD_NAME, EMULATOR_PORT, BOOT_TIMEOUT, ADB_DEADLINE)
    assert process.terminated is True
    assert clock.now >= BOOT_TIMEOUT


def test_shutdown_emulator_kills_the_process_if_it_does_not_exit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    process = _FakeProcess(wait_expires=True)
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.subprocess.run", _RunRecorder())
    shutdown_emulator(_handle(process))
    assert process.killed is True
    assert process.waited_with == SHUTDOWN_TIMEOUT_SECONDS


def test_adb_timeout_is_reported_as_an_emulator_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(args: list[str], **_kwargs: Any) -> Any:
        raise subprocess.TimeoutExpired(cmd=args, timeout=1.0)

    monkeypatch.setattr("fedact.data.lamda_apk_emulator.subprocess.run", _raise)
    with pytest.raises(AndroidEmulatorError, match="timed out"):
        shutdown_emulator(_handle())


def test_dynamic_smoke_records_launch_crash_and_observable_events(
    monkeypatch: pytest.MonkeyPatch, clock: _Clock
) -> None:
    recorder = _RunRecorder(
        [
            _completed(),
            _completed(stdout=b"Success"),
            _completed(),
            _completed(stdout=b"Events injected: 1"),
            _completed(),
            _completed(stdout=CLEAN_LOGCAT),
            _completed(),
        ]
    )
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.subprocess.run", recorder)
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.time.sleep", clock.sleep)

    result = run_dynamic_smoke(_handle(), Path("/tmp/source.apk"), PACKAGE_NAME, 25, 7)
    assert result.launched is True
    assert result.crashed_or_anr is False
    assert ObservableEvent("start:com.example.app/.MainActivity") in result.observable_events
    assert ObservableEvent("displayed:com.example.app") in result.observable_events
    assert recorder.calls[1][-2:] == ["-r", "/tmp/source.apk"]
    assert "25" in recorder.calls[4]
    assert "-s" in recorder.calls[4]


def test_dynamic_smoke_flags_a_crash_in_the_logcat(
    monkeypatch: pytest.MonkeyPatch, clock: _Clock
) -> None:
    recorder = _RunRecorder(
        [
            _completed(),
            _completed(stdout=b"Success"),
            _completed(),
            _completed(stdout=b"Events injected: 1"),
            _completed(),
            _completed(stdout=CRASH_LOGCAT),
            _completed(),
        ]
    )
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.subprocess.run", recorder)
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.time.sleep", clock.sleep)

    result = run_dynamic_smoke(_handle(), Path("/tmp/source.apk"), PACKAGE_NAME, 25, 7)
    assert result.crashed_or_anr is True


def test_dynamic_smoke_fails_when_the_apk_cannot_be_installed(
    monkeypatch: pytest.MonkeyPatch, clock: _Clock
) -> None:
    recorder = _RunRecorder([_completed(), _completed(stdout=b"Failure [INSTALL_FAILED]")])
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.subprocess.run", recorder)
    monkeypatch.setattr("fedact.data.lamda_apk_emulator.time.sleep", clock.sleep)

    with pytest.raises(AndroidEmulatorError, match="failed to install"):
        run_dynamic_smoke(_handle(), Path("/tmp/source.apk"), PACKAGE_NAME, 25, 7)


def test_jaccard_similarity_of_identical_event_sets_is_one() -> None:
    events = frozenset({ObservableEvent("start:a"), ObservableEvent("start:b")})
    assert jaccard_similarity(events, events) == 1.0


def test_jaccard_similarity_of_disjoint_event_sets_is_zero() -> None:
    assert (
        jaccard_similarity(
            frozenset({ObservableEvent("start:a")}), frozenset({ObservableEvent("start:b")})
        )
        == 0.0
    )


def test_jaccard_similarity_of_two_empty_event_sets_is_zero() -> None:
    assert jaccard_similarity(frozenset(), frozenset()) == 0.0
