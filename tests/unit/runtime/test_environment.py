from __future__ import annotations

from fedact.runtime.environment import base_runtime_versions, capture_environment_fingerprint


def test_base_runtime_versions_record_interpreter_and_numpy() -> None:
    versions = base_runtime_versions()
    assert "python" in versions
    assert "numpy" in versions
    assert "platform" in versions


def test_environment_fingerprint_covers_producer_path_tools() -> None:
    baseline = capture_environment_fingerprint({"cvxpy": "1.6.0"})
    assert baseline == capture_environment_fingerprint({"cvxpy": "1.6.0"})
    assert baseline != capture_environment_fingerprint({"cvxpy": "1.7.0"})
