from __future__ import annotations

from fedact.artifacts.identity import RuntimeComponentVersion
from fedact.runtime.environment import base_runtime_versions, capture_environment_fingerprint


def test_base_runtime_versions_record_interpreter_and_numpy() -> None:
    components = {version.component for version in base_runtime_versions()}
    assert "python" in components
    assert "numpy" in components
    assert "platform" in components


def test_environment_fingerprint_covers_producer_path_tools() -> None:
    baseline = capture_environment_fingerprint(
        (RuntimeComponentVersion(component="cvxpy", version="1.6.0"),)
    )
    assert baseline == capture_environment_fingerprint(
        (RuntimeComponentVersion(component="cvxpy", version="1.6.0"),)
    )
    assert baseline != capture_environment_fingerprint(
        (RuntimeComponentVersion(component="cvxpy", version="1.7.0"),)
    )
