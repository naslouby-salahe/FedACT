from __future__ import annotations

from fedact.storage.metadata import (
    MaterialDependency,
    compute_dependency_fingerprint,
    content_checksum,
    deterministic_json,
    sha256_digest,
)


def test_deterministic_json_is_stable_and_sorted() -> None:
    payload = deterministic_json({"b": 2, "a": 1})
    assert payload == '{"a":1,"b":2}'


def test_sha256_digest_is_prefixed_and_deterministic() -> None:
    first = sha256_digest(deterministic_json({"a": 1}))
    second = sha256_digest(deterministic_json({"a": 1}))
    assert first == second
    assert first.startswith("sha256:")


def test_content_checksum_hashes_bytes() -> None:
    checksum = content_checksum(b"payload")
    assert checksum == content_checksum(b"payload")
    assert checksum != content_checksum(b"other")


def test_dependency_fingerprint_is_order_independent() -> None:
    first = compute_dependency_fingerprint(
        (
            MaterialDependency(name="a", content_hash="h1"),
            MaterialDependency(name="b", content_hash="h2"),
        )
    )
    second = compute_dependency_fingerprint(
        (
            MaterialDependency(name="b", content_hash="h2"),
            MaterialDependency(name="a", content_hash="h1"),
        )
    )
    assert first == second
    assert first.startswith("sha256:")


def test_dependency_fingerprint_rejects_duplicate_names() -> None:
    try:
        compute_dependency_fingerprint(
            (
                MaterialDependency(name="a", content_hash="h1"),
                MaterialDependency(name="a", content_hash="h2"),
            )
        )
    except ValueError:
        return
    raise AssertionError("duplicate dependency names must be rejected")
