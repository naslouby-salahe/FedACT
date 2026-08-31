from __future__ import annotations

from fedact.artifacts.identity import ArtifactIdentity
from fedact.domain.records import ActivationFlag


class ArtifactDependencyIndex:
    def __init__(self) -> None:
        self._upstreams: dict[ArtifactIdentity, tuple[ArtifactIdentity, ...]] = {}
        self._inactive: set[ArtifactIdentity] = set()

    def register(
        self,
        identity: ArtifactIdentity,
        upstreams: tuple[ArtifactIdentity, ...] = (),
    ) -> None:
        self._upstreams[identity] = upstreams

    def deactivate(self, identity: ArtifactIdentity) -> None:
        self._inactive.add(identity)

    def is_active(self, identity: ArtifactIdentity) -> ActivationFlag:
        return identity not in self._inactive

    def direct_consumers(self, identity: ArtifactIdentity) -> frozenset[ArtifactIdentity]:
        return frozenset(
            consumer for consumer, upstreams in self._upstreams.items() if identity in upstreams
        )

    def descendants(self, identity: ArtifactIdentity) -> frozenset[ArtifactIdentity]:
        found: set[ArtifactIdentity] = set()
        frontier = [identity]
        while frontier:
            current = frontier.pop()
            for consumer in self.direct_consumers(current):
                if consumer not in found and consumer != identity:
                    found.add(consumer)
                    frontier.append(consumer)
        return frozenset(found)

    def invalidate(self, identity: ArtifactIdentity) -> frozenset[ArtifactIdentity]:
        self.deactivate(identity)
        newly_stale: set[ArtifactIdentity] = set()
        for descendant in self.descendants(identity):
            if self.is_active(descendant):
                self.deactivate(descendant)
                newly_stale.add(descendant)
        return frozenset(newly_stale)
