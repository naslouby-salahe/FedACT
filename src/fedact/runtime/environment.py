from __future__ import annotations

import platform
import sys

import numpy as np

from fedact.artifacts.identity import EnvironmentFingerprint, environment_fingerprint


def base_runtime_versions() -> dict[str, str]:
    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "platform": platform.platform(),
    }


def capture_environment_fingerprint(
    producer_tool_versions: dict[str, str],
) -> EnvironmentFingerprint:
    recorded = {**base_runtime_versions(), **producer_tool_versions}
    return environment_fingerprint(recorded)
