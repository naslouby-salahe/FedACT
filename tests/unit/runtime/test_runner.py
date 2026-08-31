from __future__ import annotations

from fedact.domain.enums import ArtifactBoundary
from fedact.domain.records import BoundaryFingerprint, BoundaryFingerprints
from fedact.runtime.runner import (
    IndexedArtifact,
    owned_boundaries_for_workflow,
    resolve_execution_requirements,
)
from fedact.runtime.status import ArtifactExecutionState
from fedact.storage.index import ArtifactDependencyIndex
from fedact.storage.metadata import ArtifactIdentity, DependencyFingerprint


def identity(label: str) -> ArtifactIdentity:
    return ArtifactIdentity(f"sha256:{label.zfill(64)}")


def fingerprint(label: str) -> DependencyFingerprint:
    return DependencyFingerprint(f"sha256:{label.zfill(64)}")


def boundary_fingerprints(
    *pairs: tuple[ArtifactBoundary, DependencyFingerprint],
) -> BoundaryFingerprints:
    return BoundaryFingerprints(
        entries=tuple(
            BoundaryFingerprint(boundary=boundary, dependency_fingerprint=fp)
            for boundary, fp in pairs
        )
    )


def artifact(
    label: str,
    boundary: ArtifactBoundary,
    state: ArtifactExecutionState,
    fingerprint_label: str,
) -> IndexedArtifact:
    return IndexedArtifact(
        identity=identity(label),
        boundary=boundary,
        state=state,
        dependency_fingerprint=fingerprint(fingerprint_label),
        upstream_identities=(),
    )


def test_missing_boundaries_are_recomputed() -> None:
    index = ArtifactDependencyIndex()
    plan = resolve_execution_requirements(
        required_boundaries=(ArtifactBoundary.DATASET_PREPARATION,),
        expected_fingerprints=boundary_fingerprints(
            (ArtifactBoundary.DATASET_PREPARATION, fingerprint("1"))
        ),
        indexed=(),
        index=index,
    )
    assert plan.recompute_boundaries() == (ArtifactBoundary.DATASET_PREPARATION,)


def test_compatible_complete_artifacts_are_reused_irrespective_of_origin_workflow() -> None:
    index = ArtifactDependencyIndex()
    existing = artifact(
        "a", ArtifactBoundary.PREPROCESSING_AND_SPLITS, ArtifactExecutionState.COMPLETE, "7"
    )
    plan = resolve_execution_requirements(
        required_boundaries=(ArtifactBoundary.PREPROCESSING_AND_SPLITS,),
        expected_fingerprints=boundary_fingerprints(
            (ArtifactBoundary.PREPROCESSING_AND_SPLITS, fingerprint("7"))
        ),
        indexed=(existing,),
        index=index,
    )
    assert plan.recompute_boundaries() == ()
    assert plan.reuse_identities() == (identity("a"),)


def test_changed_material_dependency_invalidates_nearest_boundary_and_descendants_only() -> None:
    index = ArtifactDependencyIndex()
    scores = artifact(
        "s", ArtifactBoundary.SCORING_AND_SUMMARIES, ArtifactExecutionState.COMPLETE, "old"
    )
    calibration = IndexedArtifact(
        identity=identity("c"),
        boundary=ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
        state=ArtifactExecutionState.COMPLETE,
        dependency_fingerprint=fingerprint("cal"),
        upstream_identities=(scores.identity,),
    )
    index.register(scores.identity, ())
    index.register(calibration.identity, (scores.identity,))

    plan = resolve_execution_requirements(
        required_boundaries=(ArtifactBoundary.SCORING_AND_SUMMARIES,),
        expected_fingerprints=boundary_fingerprints(
            (ArtifactBoundary.SCORING_AND_SUMMARIES, fingerprint("new"))
        ),
        indexed=(scores, calibration),
        index=index,
    )

    assert plan.recompute_boundaries() == (ArtifactBoundary.SCORING_AND_SUMMARIES,)
    assert not index.is_active(calibration.identity), (
        "stale descendant may not silently remain active"
    )


def test_stale_artifacts_are_not_reused() -> None:
    index = ArtifactDependencyIndex()
    stale = artifact("x", ArtifactBoundary.TRAINING_CHECKPOINTS, ArtifactExecutionState.STALE, "9")
    plan = resolve_execution_requirements(
        required_boundaries=(ArtifactBoundary.TRAINING_CHECKPOINTS,),
        expected_fingerprints=boundary_fingerprints(
            (ArtifactBoundary.TRAINING_CHECKPOINTS, fingerprint("9"))
        ),
        indexed=(stale,),
        index=index,
    )
    assert plan.recompute_boundaries() == (ArtifactBoundary.TRAINING_CHECKPOINTS,)


def test_overwrite_forces_only_the_command_owned_scope() -> None:
    index = ArtifactDependencyIndex()
    shared = artifact(
        "p", ArtifactBoundary.PREPROCESSING_AND_SPLITS, ArtifactExecutionState.COMPLETE, "5"
    )
    plan = resolve_execution_requirements(
        required_boundaries=(
            ArtifactBoundary.PREPROCESSING_AND_SPLITS,
            ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
        ),
        expected_fingerprints=boundary_fingerprints(
            (ArtifactBoundary.PREPROCESSING_AND_SPLITS, fingerprint("5")),
            (ArtifactBoundary.CALIBRATION_AND_CERTIFICATION, fingerprint("6")),
        ),
        indexed=(shared,),
        index=index,
        overwrite_boundaries=frozenset({ArtifactBoundary.CALIBRATION_AND_CERTIFICATION}),
    )
    decisions = {decision.boundary: decision for decision in plan.decisions}
    assert decisions[ArtifactBoundary.PREPROCESSING_AND_SPLITS].action == "reuse"
    assert decisions[ArtifactBoundary.CALIBRATION_AND_CERTIFICATION].action == "recompute"


def test_upstream_must_be_active_and_complete_for_reuse() -> None:
    index = ArtifactDependencyIndex()
    parent = artifact(
        "p", ArtifactBoundary.PREPROCESSING_AND_SPLITS, ArtifactExecutionState.COMPLETE, "5"
    )
    child = IndexedArtifact(
        identity=identity("c"),
        boundary=ArtifactBoundary.TRAINING_CHECKPOINTS,
        state=ArtifactExecutionState.COMPLETE,
        dependency_fingerprint=fingerprint("8"),
        upstream_identities=(parent.identity,),
    )
    index.register(parent.identity, ())
    index.register(child.identity, (parent.identity,))
    index.deactivate(parent.identity)

    plan = resolve_execution_requirements(
        required_boundaries=(ArtifactBoundary.TRAINING_CHECKPOINTS,),
        expected_fingerprints=boundary_fingerprints(
            (ArtifactBoundary.TRAINING_CHECKPOINTS, fingerprint("8"))
        ),
        indexed=(parent, child),
        index=index,
    )
    assert plan.recompute_boundaries() == (ArtifactBoundary.TRAINING_CHECKPOINTS,)


def test_owned_scopes_cover_the_locked_commands() -> None:
    from fedact.domain.enums import ExecutableWorkflowName as W

    assert owned_boundaries_for_workflow(W.NESTED_CALIBRATION) == (
        ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
    )
    assert owned_boundaries_for_workflow(W.STATISTICAL_SYNTHESIS) == (ArtifactBoundary.ANALYSIS,)
    assert owned_boundaries_for_workflow(W.PREPROCESS) == (
        ArtifactBoundary.DATASET_PREPARATION,
        ArtifactBoundary.PREPROCESSING_AND_SPLITS,
    )
    assert owned_boundaries_for_workflow(W.MATH_VERIFICATION) == ()
