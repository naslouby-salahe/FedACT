from __future__ import annotations

import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from fedact.data.lamda_apk_mutations import java_subprocess_environment
from fedact.domain.types import (
    AndroidAvdName,
    AndroidDeviceSerial,
    AndroidPackageName,
    AndroidSystemImage,
    EmulatorPort,
    EmulatorProcess,
    MetricRate,
    MonkeyEventCount,
    ObservableEvent,
    SeedValue,
    SubprocessEnvironment,
    TimeoutSeconds,
    ToolchainComponent,
    ValidationFlag,
)

ANDROID_SDK_ROOT_ENVIRONMENT_VARIABLE = "ANDROID_SDK_ROOT"

DEFAULT_AVD_NAME = AndroidAvdName("fedact-operator-validation")

_SDK_TOOL_RELATIVE_PATHS = {
    ToolchainComponent.ADB: Path("platform-tools") / "adb",
    ToolchainComponent.AVDMANAGER: Path("cmdline-tools") / "latest" / "bin" / "avdmanager",
    ToolchainComponent.EMULATOR: Path("emulator") / "emulator",
}


def _sdk_tool_path(sdk_root: Path, component: ToolchainComponent) -> Path:
    return sdk_root / _SDK_TOOL_RELATIVE_PATHS[component]


_EMULATOR_DEVICE_NAME = "pixel"
_MONKEY_EVENT_THROTTLE_MILLISECONDS = 50

_EMULATOR_SHUTDOWN_TIMEOUT_SECONDS = 30.0
_EMULATOR_BOOT_POLL_INTERVAL_SECONDS = 5.0
_POST_LAUNCH_SETTLE_SECONDS = 2.0

_CRASH_OR_ANR_PATTERN = re.compile(r"FATAL EXCEPTION|ANR in ")
_ACTIVITY_START_PATTERN = re.compile(r"START u0 \{[^}]*cmp=([\w.$/]+)")
_DISPLAYED_PATTERN = re.compile(r"Displayed ([\w.]+)/")


class AndroidEmulatorError(RuntimeError):
    pass


def android_sdk_root_from_environment() -> Path:
    value = os.environ.get(ANDROID_SDK_ROOT_ENVIRONMENT_VARIABLE)
    if not value:
        raise AndroidEmulatorError(
            f"{ANDROID_SDK_ROOT_ENVIRONMENT_VARIABLE} is not set in the environment"
        )
    return Path(value)


def _cmdline_tools_environment(java_home: Path) -> SubprocessEnvironment:
    environment = java_subprocess_environment()
    environment["JAVA_HOME"] = java_home.as_posix()
    return environment


@dataclass(frozen=True)
class EmulatorHandle:
    sdk_root: Path
    serial: AndroidDeviceSerial
    adb_deadline_seconds: TimeoutSeconds
    process: EmulatorProcess


def _adb(
    sdk_root: Path,
    serial: AndroidDeviceSerial,
    adb_deadline_seconds: TimeoutSeconds,
    *args: str,
) -> subprocess.CompletedProcess[bytes]:
    adb_path = _sdk_tool_path(sdk_root, ToolchainComponent.ADB)
    try:
        return subprocess.run(
            [adb_path, "-s", serial, *args],
            capture_output=True,
            check=False,
            env=java_subprocess_environment(),
            timeout=adb_deadline_seconds,
        )
    except subprocess.TimeoutExpired as error:
        raise AndroidEmulatorError(f"adb command timed out: {args}") from error


def ensure_avd(
    sdk_root: Path,
    avd_name: AndroidAvdName,
    system_image: AndroidSystemImage,
    java_home: Path,
) -> None:
    avdmanager_path = _sdk_tool_path(sdk_root, ToolchainComponent.AVDMANAGER)
    list_result = subprocess.run(
        [avdmanager_path, "list", "avd"],
        capture_output=True,
        check=True,
        env=_cmdline_tools_environment(java_home),
    )
    if avd_name in list_result.stdout.decode(errors="replace"):
        return
    create = subprocess.run(
        [
            avdmanager_path,
            "create",
            "avd",
            "--name",
            avd_name,
            "--package",
            system_image,
            "--device",
            _EMULATOR_DEVICE_NAME,
        ],
        input=b"no\n",
        capture_output=True,
        check=False,
        env=_cmdline_tools_environment(java_home),
    )
    if create.returncode != 0:
        raise AndroidEmulatorError(
            f"avdmanager create avd failed: {create.stderr.decode(errors='replace')}"
        )


def boot_emulator(
    sdk_root: Path,
    avd_name: AndroidAvdName,
    port: EmulatorPort,
    boot_timeout_seconds: TimeoutSeconds,
    adb_deadline_seconds: TimeoutSeconds,
) -> EmulatorHandle:
    emulator_path = _sdk_tool_path(sdk_root, ToolchainComponent.EMULATOR)
    serial = AndroidDeviceSerial(f"emulator-{port}")
    process = subprocess.Popen(
        [
            emulator_path,
            "-avd",
            avd_name,
            "-port",
            f"{port}",
            "-no-window",
            "-no-audio",
            "-no-boot-anim",
            "-gpu",
            "swiftshader_indirect",
            "-no-snapshot",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=java_subprocess_environment(),
    )
    deadline = time.monotonic() + boot_timeout_seconds
    booted = False
    while time.monotonic() < deadline:
        result = _adb(
            sdk_root, serial, adb_deadline_seconds, "shell", "getprop", "sys.boot_completed"
        )
        if result.stdout.decode(errors="replace").strip() == "1":
            booted = True
            break
        time.sleep(_EMULATOR_BOOT_POLL_INTERVAL_SECONDS)
    if not booted:
        process.terminate()
        raise AndroidEmulatorError(f"emulator {serial} did not boot within {boot_timeout_seconds}s")
    return EmulatorHandle(
        sdk_root=sdk_root,
        serial=serial,
        adb_deadline_seconds=adb_deadline_seconds,
        process=EmulatorProcess(process),
    )


def shutdown_emulator(emulator: EmulatorHandle) -> None:
    _adb(emulator.sdk_root, emulator.serial, emulator.adb_deadline_seconds, "emu", "kill")
    try:
        emulator.process.wait(timeout=_EMULATOR_SHUTDOWN_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        emulator.process.kill()


def _install(emulator: EmulatorHandle, apk_path: Path) -> ValidationFlag:
    result = _adb(
        emulator.sdk_root,
        emulator.serial,
        emulator.adb_deadline_seconds,
        "install",
        "-r",
        apk_path.as_posix(),
    )
    return b"Success" in result.stdout


def _uninstall(emulator: EmulatorHandle, package_name: AndroidPackageName) -> None:
    _adb(
        emulator.sdk_root, emulator.serial, emulator.adb_deadline_seconds, "uninstall", package_name
    )


def _clear_logcat(emulator: EmulatorHandle) -> None:
    _adb(emulator.sdk_root, emulator.serial, emulator.adb_deadline_seconds, "logcat", "-c")


def _launch(emulator: EmulatorHandle, package_name: AndroidPackageName) -> ValidationFlag:
    result = _adb(
        emulator.sdk_root,
        emulator.serial,
        emulator.adb_deadline_seconds,
        "shell",
        "monkey",
        "-p",
        package_name,
        "-c",
        "android.intent.category.LAUNCHER",
        "1",
    )
    return b"Events injected: 1" in result.stdout


def _run_monkey_events(
    emulator: EmulatorHandle,
    package_name: AndroidPackageName,
    event_count: MonkeyEventCount,
    seed: SeedValue,
) -> None:
    _adb(
        emulator.sdk_root,
        emulator.serial,
        emulator.adb_deadline_seconds,
        "shell",
        "monkey",
        "-p",
        package_name,
        "-s",
        f"{seed}",
        "--throttle",
        f"{_MONKEY_EVENT_THROTTLE_MILLISECONDS}",
        f"{event_count}",
    )


def _read_logcat(emulator: EmulatorHandle) -> str:
    result = _adb(emulator.sdk_root, emulator.serial, emulator.adb_deadline_seconds, "logcat", "-d")
    return result.stdout.decode(errors="replace")


def _observable_event_set(logcat_text: str) -> frozenset[ObservableEvent]:
    events: set[ObservableEvent] = set()
    for match in _ACTIVITY_START_PATTERN.finditer(logcat_text):
        events.add(ObservableEvent(f"start:{match.group(1)}"))
    for match in _DISPLAYED_PATTERN.finditer(logcat_text):
        events.add(ObservableEvent(f"displayed:{match.group(1)}"))
    return frozenset(events)


def _has_crash_or_anr(logcat_text: str) -> ValidationFlag:
    return _CRASH_OR_ANR_PATTERN.search(logcat_text) is not None


@dataclass(frozen=True)
class DynamicRunResult:
    launched: ValidationFlag
    crashed_or_anr: ValidationFlag
    observable_events: frozenset[ObservableEvent]


def run_dynamic_smoke(
    emulator: EmulatorHandle,
    apk_path: Path,
    package_name: AndroidPackageName,
    monkey_event_count: MonkeyEventCount,
    monkey_seed: SeedValue,
) -> DynamicRunResult:
    _uninstall(emulator, package_name)
    if not _install(emulator, apk_path):
        raise AndroidEmulatorError(f"failed to install {apk_path} for dynamic validation")
    _clear_logcat(emulator)
    launched = _launch(emulator, package_name)
    time.sleep(_POST_LAUNCH_SETTLE_SECONDS)
    _run_monkey_events(emulator, package_name, monkey_event_count, monkey_seed)
    time.sleep(_POST_LAUNCH_SETTLE_SECONDS)
    logcat_text = _read_logcat(emulator)
    result = DynamicRunResult(
        launched=launched,
        crashed_or_anr=_has_crash_or_anr(logcat_text),
        observable_events=_observable_event_set(logcat_text),
    )
    _uninstall(emulator, package_name)
    return result


def jaccard_similarity(
    source_events: frozenset[ObservableEvent], transformed_events: frozenset[ObservableEvent]
) -> MetricRate:
    union = source_events | transformed_events
    if not union:
        return 0.0
    intersection = source_events & transformed_events
    return len(intersection) / len(union)
