from __future__ import annotations

from dataclasses import dataclass

from fedact.domain.enums import ArtifactBoundary, ExecutableWorkflowName
from fedact.domain.records import ActionDecision, BoundaryFingerprints, ExecutionReason
from fedact.runtime.status import ArtifactExecutionState
from fedact.storage.index import ArtifactDependencyIndex
from fedact.storage.metadata import ArtifactIdentity, DependencyFingerprint


@dataclass(frozen=True)
class IndexedArtifact:
    identity: ArtifactIdentity
    boundary: ArtifactBoundary
    state: ArtifactExecutionState
    dependency_fingerprint: DependencyFingerprint
    upstream_identities: tuple[ArtifactIdentity, ...]


@dataclass(frozen=True)
class BoundaryDecision:
    boundary: ArtifactBoundary
    action: ActionDecision
    reused_identity: ArtifactIdentity | None
    reason: ExecutionReason


@dataclass(frozen=True)
class ResolutionPlan:
    decisions: tuple[BoundaryDecision, ...]
    newly_stale: tuple[ArtifactIdentity, ...]

    def recompute_boundaries(self) -> tuple[ArtifactBoundary, ...]:
        return tuple(
            decision.boundary for decision in self.decisions if decision.action == "recompute"
        )

    def reuse_identities(self) -> tuple[ArtifactIdentity, ...]:
        return tuple(
            decision.reused_identity
            for decision in self.decisions
            if decision.action == "reuse" and decision.reused_identity is not None
        )


EXECUTABLE_WORKFLOW_BOUNDARY_MAP: dict[ExecutableWorkflowName, tuple[ArtifactBoundary, ...]] = {
    ExecutableWorkflowName.PREPROCESS: (
        ArtifactBoundary.DATASET_PREPARATION,
        ArtifactBoundary.PREPROCESSING_AND_SPLITS,
    ),
    ExecutableWorkflowName.BASELINE_PARITY: (ArtifactBoundary.TRAINING_CHECKPOINTS,),
    ExecutableWorkflowName.NESTED_CALIBRATION: (ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,),
    ExecutableWorkflowName.PROSPECTIVE_EVALUATION: (ArtifactBoundary.EVALUATION,),
    ExecutableWorkflowName.STATISTICAL_SYNTHESIS: (ArtifactBoundary.ANALYSIS,),
}


def owned_boundaries_for_workflow(
    workflow: ExecutableWorkflowName,
) -> tuple[ArtifactBoundary, ...]:
    return EXECUTABLE_WORKFLOW_BOUNDARY_MAP.get(workflow, ())


def _active_candidate_for_boundary(
    boundary: ArtifactBoundary,
    indexed: tuple[IndexedArtifact, ...],
    index: ArtifactDependencyIndex,
    expected_fingerprint: DependencyFingerprint | None,
) -> IndexedArtifact | None:
    candidates = [
        artifact
        for artifact in indexed
        if artifact.boundary is boundary
        and artifact.state is ArtifactExecutionState.COMPLETE
        and (
            expected_fingerprint is None or artifact.dependency_fingerprint == expected_fingerprint
        )
        and index.is_active(artifact.identity)
        and all(index.is_active(upstream) for upstream in artifact.upstream_identities)
    ]
    if not candidates:
        return None
    return candidates[0]


def _normalize_indexed(
    indexed: tuple[IndexedArtifact, ...] | None,
    indexed_artifacts: tuple[IndexedArtifact, ...] | None,
) -> tuple[IndexedArtifact, ...]:
    if indexed is not None:
        return indexed
    if indexed_artifacts is not None:
        return indexed_artifacts
    return ()


def _normalize_index(
    index: ArtifactDependencyIndex | None,
    dependency_index: ArtifactDependencyIndex | None,
) -> ArtifactDependencyIndex:
    if index is not None:
        return index
    if dependency_index is not None:
        return dependency_index
    return ArtifactDependencyIndex()


def _deactivate_mismatches(
    actual_indexed: tuple[IndexedArtifact, ...],
    actual_index: ArtifactDependencyIndex,
    expected_fingerprints: BoundaryFingerprints,
) -> None:
    for candidate_artifact in actual_indexed:
        exp_fp = expected_fingerprints.for_boundary(candidate_artifact.boundary)
        if exp_fp is not None and candidate_artifact.dependency_fingerprint != exp_fp:
            actual_index.deactivate(candidate_artifact.identity)
            for desc in actual_index.descendants(candidate_artifact.identity):
                actual_index.deactivate(desc)


def resolve_execution_requirements(
    required_boundaries: tuple[ArtifactBoundary, ...],
    indexed: tuple[IndexedArtifact, ...] | None = None,
    index: ArtifactDependencyIndex | None = None,
    expected_fingerprints: BoundaryFingerprints | None = None,
    force_recompute_boundaries: frozenset[ArtifactBoundary] = frozenset(),
    overwrite_boundaries: frozenset[ArtifactBoundary] = frozenset(),
    indexed_artifacts: tuple[IndexedArtifact, ...] | None = None,
    dependency_index: ArtifactDependencyIndex | None = None,
) -> ResolutionPlan:
    actual_indexed = _normalize_indexed(indexed, indexed_artifacts)
    actual_index = _normalize_index(index, dependency_index)
    actual_expected_fingerprints = expected_fingerprints or BoundaryFingerprints()

    decisions: list[BoundaryDecision] = []
    newly_stale: list[ArtifactIdentity] = []
    recompute_cascading = False
    forces = force_recompute_boundaries | overwrite_boundaries

    if actual_expected_fingerprints:
        _deactivate_mismatches(actual_indexed, actual_index, actual_expected_fingerprints)

    for boundary in required_boundaries:
        expected_fp = actual_expected_fingerprints.for_boundary(boundary)
        candidate = _active_candidate_for_boundary(
            boundary, actual_indexed, actual_index, expected_fp
        )
        must_recompute = boundary in forces or recompute_cascading or candidate is None
        if must_recompute:
            recompute_cascading = True
            if candidate is not None and boundary in forces:
                newly_stale.append(candidate.identity)
            reason = "forced" if boundary in forces else "upstream_modified_or_missing"
            decisions.append(
                BoundaryDecision(
                    boundary=boundary,
                    action="recompute",
                    reused_identity=None,
                    reason=reason,
                )
            )
        else:
            assert candidate is not None
            decisions.append(
                BoundaryDecision(
                    boundary=boundary,
                    action="reuse",
                    reused_identity=candidate.identity,
                    reason="fingerprint_matched_active",
                )
            )
    return ResolutionPlan(decisions=tuple(decisions), newly_stale=tuple(newly_stale))
