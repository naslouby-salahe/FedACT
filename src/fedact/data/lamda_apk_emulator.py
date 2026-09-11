from __future__ import annotations

import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from fedact.data.lamda_apk_mutations import java_subprocess_environment

ANDROID_SDK_ROOT_ENVIRONMENT_VARIABLE = "ANDROID_SDK_ROOT"
_CMDLINE_TOOLS_JAVA_HOME = "/usr/lib/jvm/java-17-openjdk-amd64"

DEFAULT_AVD_NAME = "fedact-operator-validation"
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


def _cmdline_tools_environment() -> dict[str, str]:
    environment = java_subprocess_environment()
    environment["JAVA_HOME"] = _CMDLINE_TOOLS_JAVA_HOME
    return environment


@dataclass(frozen=True)
class EmulatorHandle:
    sdk_root: Path
    serial: str
    process: subprocess.Popen[bytes]


_DEFAULT_ADB_TIMEOUT_SECONDS = 60.0


def _adb(
    sdk_root: Path,
    serial: str,
    *args: str,
    timeout_seconds: float = _DEFAULT_ADB_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[bytes]:
    adb_path = sdk_root / "platform-tools" / "adb"
    try:
        return subprocess.run(
            [str(adb_path), "-s", serial, *args],
            capture_output=True,
            check=False,
            env=java_subprocess_environment(),
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        raise AndroidEmulatorError(f"adb command timed out: {args}") from error


def ensure_avd(sdk_root: Path, avd_name: str, system_image: str) -> None:
    avdmanager_path = sdk_root / "cmdline-tools" / "latest" / "bin" / "avdmanager"
    list_result = subprocess.run(
        [str(avdmanager_path), "list", "avd"],
        capture_output=True,
        check=True,
        env=_cmdline_tools_environment(),
    )
    if avd_name in list_result.stdout.decode(errors="replace"):
        return
    create = subprocess.run(
        [
            str(avdmanager_path),
            "create",
            "avd",
            "--name",
            avd_name,
            "--package",
            system_image,
            "--device",
            "pixel",
        ],
        input=b"no\n",
        capture_output=True,
        check=False,
        env=_cmdline_tools_environment(),
    )
    if create.returncode != 0:
        raise AndroidEmulatorError(
            f"avdmanager create avd failed: {create.stderr.decode(errors='replace')}"
        )


def boot_emulator(
    sdk_root: Path, avd_name: str, port: int, boot_timeout_seconds: float
) -> EmulatorHandle:
    emulator_path = sdk_root / "emulator" / "emulator"
    serial = f"emulator-{port}"
    process = subprocess.Popen(
        [
            str(emulator_path),
            "-avd",
            avd_name,
            "-port",
            str(port),
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
        result = _adb(sdk_root, serial, "shell", "getprop", "sys.boot_completed")
        if result.stdout.decode(errors="replace").strip() == "1":
            booted = True
            break
        time.sleep(5)
    if not booted:
        process.terminate()
        raise AndroidEmulatorError(f"emulator {serial} did not boot within {boot_timeout_seconds}s")
    return EmulatorHandle(sdk_root=sdk_root, serial=serial, process=process)


def shutdown_emulator(handle: EmulatorHandle) -> None:
    _adb(handle.sdk_root, handle.serial, "emu", "kill")
    try:
        handle.process.wait(timeout=30)
    except subprocess.TimeoutExpired:
        handle.process.kill()


def _install(handle: EmulatorHandle, apk_path: Path) -> bool:
    result = _adb(handle.sdk_root, handle.serial, "install", "-r", str(apk_path))
    return b"Success" in result.stdout


def _uninstall(handle: EmulatorHandle, package_name: str) -> None:
    _adb(handle.sdk_root, handle.serial, "uninstall", package_name)


def _clear_logcat(handle: EmulatorHandle) -> None:
    _adb(handle.sdk_root, handle.serial, "logcat", "-c")


def _launch(handle: EmulatorHandle, package_name: str) -> bool:
    result = _adb(
        handle.sdk_root,
        handle.serial,
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
    handle: EmulatorHandle, package_name: str, event_count: int, seed: int
) -> None:
    _adb(
        handle.sdk_root,
        handle.serial,
        "shell",
        "monkey",
        "-p",
        package_name,
        "-s",
        str(seed),
        "--throttle",
        "50",
        str(event_count),
    )


def _read_logcat(handle: EmulatorHandle) -> str:
    result = _adb(handle.sdk_root, handle.serial, "logcat", "-d")
    return result.stdout.decode(errors="replace")


def _observable_event_set(logcat_text: str) -> frozenset[str]:
    events: set[str] = set()
    for match in _ACTIVITY_START_PATTERN.finditer(logcat_text):
        events.add(f"start:{match.group(1)}")
    for match in _DISPLAYED_PATTERN.finditer(logcat_text):
        events.add(f"displayed:{match.group(1)}")
    return frozenset(events)


def _has_crash_or_anr(logcat_text: str) -> bool:
    return _CRASH_OR_ANR_PATTERN.search(logcat_text) is not None


@dataclass(frozen=True)
class DynamicRunResult:
    launched: bool
    crashed_or_anr: bool
    observable_events: frozenset[str]


def run_dynamic_smoke(
    handle: EmulatorHandle,
    apk_path: Path,
    package_name: str,
    monkey_event_count: int,
    monkey_seed: int,
) -> DynamicRunResult:
    _uninstall(handle, package_name)
    if not _install(handle, apk_path):
        raise AndroidEmulatorError(f"failed to install {apk_path} for dynamic validation")
    _clear_logcat(handle)
    launched = _launch(handle, package_name)
    time.sleep(2)
    _run_monkey_events(handle, package_name, monkey_event_count, monkey_seed)
    time.sleep(2)
    logcat_text = _read_logcat(handle)
    result = DynamicRunResult(
        launched=launched,
        crashed_or_anr=_has_crash_or_anr(logcat_text),
        observable_events=_observable_event_set(logcat_text),
    )
    _uninstall(handle, package_name)
    return result


def jaccard_similarity(source_events: frozenset[str], transformed_events: frozenset[str]) -> float:
    union = source_events | transformed_events
    if not union:
        return 0.0
    intersection = source_events & transformed_events
    return len(intersection) / len(union)
