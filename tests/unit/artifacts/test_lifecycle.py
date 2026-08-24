from __future__ import annotations

import pytest

from fedact.artifacts.lifecycle import (
    LEGAL_TRANSITIONS,
    ArtifactCompletionError,
    IllegalArtifactTransitionError,
    is_reusable,
    validate_completion,
    validate_transition,
)
from fedact.domain.enums import ArtifactLifecycleState as State
from fedact.domain.records import CompletionEvidence, CompletionRequirements


def test_legal_transitions_match_the_locked_lifecycle() -> None:
    assert LEGAL_TRANSITIONS[State.PLANNED] == frozenset({State.STAGING})
    assert LEGAL_TRANSITIONS[State.STAGING] == frozenset({State.COMPLETE, State.INCOMPLETE})
    assert LEGAL_TRANSITIONS[State.COMPLETE] == frozenset({State.REUSED, State.STALE})
    assert LEGAL_TRANSITIONS[State.REUSED] == frozenset({State.STALE})
    assert LEGAL_TRANSITIONS[State.STALE] == frozenset({State.REPLACED, State.CLEANED})
    assert LEGAL_TRANSITIONS[State.INCOMPLETE] == frozenset({State.CLEANED})
    assert LEGAL_TRANSITIONS[State.REPLACED] == frozenset()
    assert LEGAL_TRANSITIONS[State.CLEANED] == frozenset()


def test_illegal_transitions_are_rejected() -> None:
    for current, targets in LEGAL_TRANSITIONS.items():
        for target in State:
            if target in targets or target is current:
                continue
            with pytest.raises(IllegalArtifactTransitionError):
                validate_transition(current, target)


def test_legal_transition_path_is_accepted() -> None:
    validate_transition(State.PLANNED, State.STAGING)
    validate_transition(State.STAGING, State.COMPLETE)
    validate_transition(State.COMPLETE, State.REUSED)
    validate_transition(State.REUSED, State.STALE)
    validate_transition(State.STALE, State.REPLACED)


def test_only_complete_states_are_reusable() -> None:
    assert is_reusable(State.COMPLETE)
    assert is_reusable(State.REUSED)
    assert not is_reusable(State.PLANNED)
    assert not is_reusable(State.STAGING)
    assert not is_reusable(State.STALE)
    assert not is_reusable(State.INCOMPLETE)
    assert not is_reusable(State.REPLACED)
    assert not is_reusable(State.CLEANED)


def _requirements() -> CompletionRequirements:
    return CompletionRequirements(
        required_files=frozenset({"payload.bin", "manifest.json"}),
        required_manifest_fields=frozenset({"artifact_id", "configuration_hash"}),
        required_integrity_checks=frozenset({"sha256_payload"}),
        required_scientific_invariants=frozenset({"coverage_invariant"}),
    )


def _evidence(
    present_files: frozenset[str] = frozenset({"payload.bin", "manifest.json"}),
    populated_manifest_fields: frozenset[str] = frozenset({"artifact_id", "configuration_hash"}),
    passed_integrity_checks: frozenset[str] = frozenset({"sha256_payload"}),
    passed_scientific_invariants: frozenset[str] = frozenset({"coverage_invariant"}),
    completion_record_committed: bool = True,
) -> CompletionEvidence:
    return CompletionEvidence(
        present_files=present_files,
        populated_manifest_fields=populated_manifest_fields,
        passed_integrity_checks=passed_integrity_checks,
        passed_scientific_invariants=passed_scientific_invariants,
        completion_record_committed=completion_record_committed,
    )


def test_complete_evidence_passes_completion_validation() -> None:
    validate_completion(_requirements(), _evidence())


def test_missing_required_file_blocks_completion() -> None:
    reqs = _requirements()
    evidence = _evidence(present_files=frozenset({"payload.bin"}))
    with pytest.raises(ArtifactCompletionError, match="required files"):
        validate_completion(reqs, evidence)


def test_missing_manifest_field_blocks_completion() -> None:
    reqs = _requirements()
    evidence = _evidence(populated_manifest_fields=frozenset({"artifact_id"}))
    with pytest.raises(ArtifactCompletionError, match="manifest fields"):
        validate_completion(reqs, evidence)


def test_failed_integrity_check_blocks_completion() -> None:
    reqs = _requirements()
    evidence = _evidence(passed_integrity_checks=frozenset())
    with pytest.raises(ArtifactCompletionError, match="integrity"):
        validate_completion(reqs, evidence)


def test_failed_scientific_invariant_blocks_completion() -> None:
    reqs = _requirements()
    evidence = _evidence(passed_scientific_invariants=frozenset())
    with pytest.raises(ArtifactCompletionError, match="scientific invariants"):
        validate_completion(reqs, evidence)


def test_uncommitted_completion_record_blocks_reusability() -> None:
    reqs = _requirements()
    evidence = _evidence(completion_record_committed=False)
    with pytest.raises(ArtifactCompletionError, match="atomically committed"):
        validate_completion(reqs, evidence)
