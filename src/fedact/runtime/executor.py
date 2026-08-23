from __future__ import annotations

from dataclasses import dataclass

from fedact.artifacts.dependencies import ArtifactDependencyIndex
from fedact.artifacts.identity import ArtifactIdentity, DependencyFingerprint
from fedact.domain.enums import ArtifactBoundary, ExecutableWorkflowName
from fedact.runtime.state import ArtifactExecutionState


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
    action: str
    reused_identity: ArtifactIdentity | None
    reason: str


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


def _active_candidate_for_boundary(
    boundary: ArtifactBoundary,
    indexed: tuple[IndexedArtifact, ...],
    index: ArtifactDependencyIndex,
    expected_fingerprint: DependencyFingerprint,
) -> IndexedArtifact | None:
    candidates = [
        artifact
        for artifact in indexed
        if artifact.boundary is boundary
        and artifact.state is ArtifactExecutionState.COMPLETE
        and artifact.dependency_fingerprint == expected_fingerprint
        and index.is_active(artifact.identity)
    ]
    if not candidates:
        return None
    for candidate in candidates:
        upstreams_active = all(
            index.is_active(upstream) for upstream in candidate.upstream_identities
        )
        upstreams_complete = all(
            any(
                other.identity == upstream and other.state is ArtifactExecutionState.COMPLETE
                for other in indexed
            )
            for upstream in candidate.upstream_identities
        )
        if upstreams_active and upstreams_complete:
            return candidate
    return None


def resolve_execution_requirements(
    required_boundaries: tuple[ArtifactBoundary, ...],
    expected_fingerprints: dict[ArtifactBoundary, DependencyFingerprint],
    indexed: tuple[IndexedArtifact, ...],
    index: ArtifactDependencyIndex,
    overwrite_boundaries: frozenset[ArtifactBoundary] = frozenset(),
) -> ResolutionPlan:
    decisions: list[BoundaryDecision] = []
    newly_stale: list[ArtifactIdentity] = []
    for boundary in required_boundaries:
        expected = expected_fingerprints.get(boundary)
        if expected is None:
            decisions.append(
                BoundaryDecision(
                    boundary=boundary,
                    action="blocked",
                    reused_identity=None,
                    reason="no expected dependency fingerprint configured",
                )
            )
            continue
        if boundary in overwrite_boundaries:
            decisions.append(
                BoundaryDecision(
                    boundary=boundary,
                    action="recompute",
                    reused_identity=None,
                    reason="overwrite forces regeneration of this command-owned scope",
                )
            )
            continue
        candidate = _active_candidate_for_boundary(boundary, indexed, index, expected)
        if candidate is not None:
            decisions.append(
                BoundaryDecision(
                    boundary=boundary,
                    action="reuse",
                    reused_identity=candidate.identity,
                    reason="COMPLETE artifact with matching dependency fingerprint",
                )
            )
            continue
        stale_candidate = next(
            (
                artifact
                for artifact in indexed
                if artifact.boundary is boundary and artifact.dependency_fingerprint != expected
            ),
            None,
        )
        if stale_candidate is not None:
            newly_stale.extend(index.invalidate(stale_candidate.identity))
            decisions.append(
                BoundaryDecision(
                    boundary=boundary,
                    action="recompute",
                    reused_identity=None,
                    reason="dependency fingerprint changed; invalidating nearest boundary",
                )
            )
        else:
            decisions.append(
                BoundaryDecision(
                    boundary=boundary,
                    action="recompute",
                    reused_identity=None,
                    reason="no existing artifact for this boundary",
                )
            )
    return ResolutionPlan(decisions=tuple(decisions), newly_stale=tuple(newly_stale))


def owned_boundaries_for_workflow(
    workflow: ExecutableWorkflowName,
) -> tuple[ArtifactBoundary, ...]:
    mapping: dict[ExecutableWorkflowName, tuple[ArtifactBoundary, ...]] = {
        ExecutableWorkflowName.PREPROCESS: (
            ArtifactBoundary.DATASET_PREPARATION,
            ArtifactBoundary.PREPROCESSING_AND_SPLITS,
        ),
        ExecutableWorkflowName.SMOKE: (),
        ExecutableWorkflowName.BASELINE_PARITY: (ArtifactBoundary.TRAINING_CHECKPOINTS,),
        ExecutableWorkflowName.NESTED_CALIBRATION: (
            ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
        ),
        ExecutableWorkflowName.MATH_VERIFICATION: (),
        ExecutableWorkflowName.SYNTHETIC_GEOMETRY: (ArtifactBoundary.EVALUATION,),
        ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION: (ArtifactBoundary.EVALUATION,),
        ExecutableWorkflowName.PROSPECTIVE_EVALUATION: (ArtifactBoundary.EVALUATION,),
        ExecutableWorkflowName.ABLATIONS: (ArtifactBoundary.EVALUATION,),
        ExecutableWorkflowName.FEDERATION: (ArtifactBoundary.EVALUATION,),
        ExecutableWorkflowName.FAILURE_BOUNDARIES: (ArtifactBoundary.EVALUATION,),
        ExecutableWorkflowName.CROSS_CORPUS: (ArtifactBoundary.EVALUATION,),
        ExecutableWorkflowName.CLIENT_SELECTION: (ArtifactBoundary.EVALUATION,),
        ExecutableWorkflowName.STATISTICAL_SYNTHESIS: (ArtifactBoundary.ANALYSIS,),
    }
    return mapping.get(workflow, ())
