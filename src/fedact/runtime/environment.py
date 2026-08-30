from __future__ import annotations

import platform
import sys

import numpy as np

from fedact.artifacts.identity import (
    EnvironmentFingerprint,
    RuntimeComponentVersion,
    environment_fingerprint,
)


def base_runtime_versions() -> tuple[RuntimeComponentVersion, ...]:
    return (
        RuntimeComponentVersion(component="python", version=sys.version.split()[0]),
        RuntimeComponentVersion(component="numpy", version=np.__version__),
        RuntimeComponentVersion(component="platform", version=platform.platform()),
    )


def capture_environment_fingerprint(
    producer_tool_versions: tuple[RuntimeComponentVersion, ...],
) -> EnvironmentFingerprint:
    recorded = base_runtime_versions() + producer_tool_versions
    return environment_fingerprint(recorded)
