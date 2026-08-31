from __future__ import annotations

from fedact.domain.enums import ArtifactLifecycleState
from fedact.domain.records import CompletionEvidence, CompletionRequirements, ReusabilityFlag


class IllegalArtifactTransitionError(ValueError):
    pass


class ArtifactCompletionError(ValueError):
    pass


LEGAL_TRANSITIONS: dict[ArtifactLifecycleState, frozenset[ArtifactLifecycleState]] = {
    ArtifactLifecycleState.PLANNED: frozenset({ArtifactLifecycleState.STAGING}),
    ArtifactLifecycleState.STAGING: frozenset(
        {ArtifactLifecycleState.COMPLETE, ArtifactLifecycleState.INCOMPLETE}
    ),
    ArtifactLifecycleState.COMPLETE: frozenset(
        {ArtifactLifecycleState.REUSED, ArtifactLifecycleState.STALE}
    ),
    ArtifactLifecycleState.REUSED: frozenset({ArtifactLifecycleState.STALE}),
    ArtifactLifecycleState.STALE: frozenset(
        {ArtifactLifecycleState.REPLACED, ArtifactLifecycleState.CLEANED}
    ),
    ArtifactLifecycleState.INCOMPLETE: frozenset({ArtifactLifecycleState.CLEANED}),
    ArtifactLifecycleState.REPLACED: frozenset(),
    ArtifactLifecycleState.CLEANED: frozenset(),
}

REUSABLE_STATES: frozenset[ArtifactLifecycleState] = frozenset(
    {ArtifactLifecycleState.COMPLETE, ArtifactLifecycleState.REUSED}
)


def validate_transition(current: ArtifactLifecycleState, target: ArtifactLifecycleState) -> None:
    allowed = LEGAL_TRANSITIONS[current]
    if target not in allowed:
        raise IllegalArtifactTransitionError(
            f"illegal artifact lifecycle transition from {current} to {target}; "
            f"allowed targets: {sorted(allowed)}"
        )


def is_reusable(state: ArtifactLifecycleState) -> ReusabilityFlag:
    return state in REUSABLE_STATES


def validate_completion(requirements: CompletionRequirements, evidence: CompletionEvidence) -> None:
    missing_files = sorted(requirements.required_files - evidence.present_files)
    if missing_files:
        raise ArtifactCompletionError(
            f"artifact completion missing required files: {missing_files}"
        )

    missing_manifest_fields = sorted(
        requirements.required_manifest_fields - evidence.populated_manifest_fields
    )
    if missing_manifest_fields:
        raise ArtifactCompletionError(
            f"artifact completion missing required manifest fields: {missing_manifest_fields}"
        )

    failed_integrity_checks = sorted(
        requirements.required_integrity_checks - evidence.passed_integrity_checks
    )
    if failed_integrity_checks:
        raise ArtifactCompletionError(
            f"artifact completion missing passed integrity checks: {failed_integrity_checks}"
        )

    failed_scientific_invariants = sorted(
        requirements.required_scientific_invariants - evidence.passed_scientific_invariants
    )
    if failed_scientific_invariants:
        raise ArtifactCompletionError(
            "artifact completion missing passed scientific invariants: "
            f"{failed_scientific_invariants}"
        )

    if not evidence.completion_record_committed:
        raise ArtifactCompletionError(
            "artifact completion requires an atomically committed completion record"
        )
