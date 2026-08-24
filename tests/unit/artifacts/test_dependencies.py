from __future__ import annotations

from fedact.artifacts.dependencies import ArtifactDependencyIndex
from fedact.artifacts.identity import ArtifactIdentity


def identity(label: str) -> ArtifactIdentity:
    return ArtifactIdentity(f"sha256:{label.zfill(64)}")


def test_direct_consumers_are_reversed_from_registered_upstreams() -> None:
    index = ArtifactDependencyIndex()
    parent = identity("a")
    child = identity("b")
    grandchild = identity("c")
    index.register(parent, ())
    index.register(child, (parent,))
    index.register(grandchild, (child,))

    assert index.direct_consumers(parent) == frozenset({child})
    assert index.descendants(parent) == frozenset({child, grandchild})


def test_invalidation_marks_only_descendants_stale() -> None:
    index = ArtifactDependencyIndex()
    parent = identity("a")
    sibling = identity("s")
    child = identity("b")
    grandchild = identity("c")
    index.register(parent, ())
    index.register(sibling, ())
    index.register(child, (parent,))
    index.register(grandchild, (child,))

    newly_stale = index.invalidate(parent)

    assert parent not in newly_stale
    assert not index.is_active(parent)
    assert newly_stale == frozenset({child, grandchild})
    assert not index.is_active(child)
    assert not index.is_active(grandchild)
    assert index.is_active(sibling), "siblings must remain active"


def test_ancestors_are_never_invalidated() -> None:
    index = ArtifactDependencyIndex()
    root = identity("r")
    leaf = identity("l")
    index.register(root, ())
    index.register(leaf, (root,))

    index.invalidate(leaf)

    assert index.is_active(root)
