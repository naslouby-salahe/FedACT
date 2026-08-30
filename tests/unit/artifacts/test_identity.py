from __future__ import annotations

import pytest

from fedact.artifacts.identity import (
    MaterialDependency,
    compute_dependency_fingerprint,
    content_checksum,
    deterministic_json,
    environment_fingerprint,
    material_configuration_hash,
    producer_code_fingerprint,
)


def test_deterministic_json_is_stable_and_compact() -> None:
    assert deterministic_json({"b": 1, "a": [2, 3]}) == '{"a":[2,3],"b":1}'
    assert deterministic_json({"a": 1}) == '{"a":1}'


def test_content_checksum_is_deterministic_sha256() -> None:
    first = content_checksum(b"payload")
    second = content_checksum(b"payload")
    assert first == second
    assert first.startswith("sha256:")
    assert len(first) == len("sha256:") + 64
    assert first != content_checksum(b"other")


def test_dependency_fingerprint_ignores_material_dependency_order() -> None:
    left = compute_dependency_fingerprint(
        (
            MaterialDependency(name="raw_checksum", content_hash="abc"),
            MaterialDependency(name="seed", content_hash="1001"),
        )
    )
    right = compute_dependency_fingerprint(
        (
            MaterialDependency(name="seed", content_hash="1001"),
            MaterialDependency(name="raw_checksum", content_hash="abc"),
        )
    )
    assert left == right


def test_dependency_fingerprint_changes_with_any_material_dependency() -> None:
    baseline = compute_dependency_fingerprint(
        (MaterialDependency(name="seed", content_hash="1001"),)
    )
    changed = compute_dependency_fingerprint(
        (MaterialDependency(name="seed", content_hash="1002"),)
    )
    extended = compute_dependency_fingerprint(
        (
            MaterialDependency(name="seed", content_hash="1001"),
            MaterialDependency(name="cutoff", content_hash="2024-01"),
        )
    )
    assert changed != baseline
    assert extended != baseline


def test_duplicate_material_dependency_names_are_rejected() -> None:
    deps = (
        MaterialDependency(name="seed", content_hash="1001"),
        MaterialDependency(name="seed", content_hash="1002"),
    )
    with pytest.raises(ValueError):
        compute_dependency_fingerprint(deps)


def test_material_configuration_hash_depends_only_on_selected_subset() -> None:
    full_values = {"training.batch_size": "256", "reporting.p_value_display_threshold": "0.0001"}
    subset = {"training.batch_size": "256"}
    assert material_configuration_hash(subset) != material_configuration_hash(full_values)
    assert material_configuration_hash(subset).startswith("sha256:")


def test_producer_code_fingerprint_tracks_semantics_relevant_sources() -> None:
    sources = (("producer_a", "def run():\n    return 1\n"),)
    baseline = producer_code_fingerprint(sources)
    assert baseline == producer_code_fingerprint(sources)
    assert baseline != producer_code_fingerprint((("producer_a", "def run():\n    return 2\n"),))
    unrelated = (("unrelated_module", "value = 1\n"),)
    assert baseline != producer_code_fingerprint(sources + unrelated)


def test_empty_producer_source_set_is_rejected() -> None:
    with pytest.raises(ValueError):
        producer_code_fingerprint(())


def test_environment_fingerprint_sensitivity() -> None:
    baseline = environment_fingerprint({"numpy": "2.3.0"})
    assert baseline == environment_fingerprint({"numpy": "2.3.0"})
    assert baseline != environment_fingerprint({"numpy": "2.3.1"})
    assert baseline != environment_fingerprint({"numpy": "2.3.0", "cvxpy": "1.6.0"})
