from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum

from fedact.domain.records import (
    DomainValidityFlag,
    HashDigest,
    SimilarityScore,
    TimeoutSeconds,
    ToolchainIdentifier,
    ValidationFlag,
)


class ValidityStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"


class ValidityLayerError(ValueError):
    pass


@dataclass(frozen=True)
class StructuralValidity:
    parser_primary_ok: bool
    parser_secondary_ok: bool
    expected_machine_type: ValidationFlag

    @property
    def is_valid(self) -> DomainValidityFlag:
        return self.parser_primary_ok and self.parser_secondary_ok and self.expected_machine_type


@dataclass(frozen=True)
class ExecutionSmokeValidity:
    source_launched: ValidationFlag
    transformed_launched: ValidationFlag
    no_new_crash_or_anr: ValidationFlag
    sandbox_identity_recorded: bool
    within_timeout_seconds: TimeoutSeconds

    @property
    def is_valid(self) -> DomainValidityFlag:
        return (
            self.source_launched
            and self.transformed_launched
            and self.no_new_crash_or_anr
            and self.sandbox_identity_recorded
            and self.within_timeout_seconds <= 30.0
        )


@dataclass(frozen=True)
class MaliciousnessValidity:
    source_detected: ValidationFlag
    transformed_detected: ValidationFlag

    @property
    def is_valid(self) -> DomainValidityFlag:
        return self.source_detected and self.transformed_detected


@dataclass(frozen=True)
class BehaviorValidity:
    jaccard_similarity: SimilarityScore
    minimum_behavior_jaccard: SimilarityScore
    both_event_sets_empty: ValidationFlag

    @property
    def is_valid(self) -> DomainValidityFlag:
        if self.both_event_sets_empty:
            return False
        return self.jaccard_similarity >= self.minimum_behavior_jaccard


@dataclass(frozen=True)
class CandidateValidityRecord:
    structural: StructuralValidity
    smoke: ExecutionSmokeValidity
    maliciousness: MaliciousnessValidity
    behavior: BehaviorValidity
    toolchain_identity: ToolchainIdentifier
    source_hash: HashDigest

    @property
    def status(self) -> ValidityStatus:
        all_valid = (
            self.structural.is_valid
            and self.smoke.is_valid
            and self.maliciousness.is_valid
            and self.behavior.is_valid
        )
        return ValidityStatus.VALID if all_valid else ValidityStatus.INVALID


def require_all_four_layers(record: CandidateValidityRecord) -> ValidationFlag:
    if record.status is not ValidityStatus.VALID:
        raise ValidityLayerError("Candidate failed 4-layer validity")
    return True


def validate_candidate_displacements(
    candidates: Sequence[CandidateValidityRecord],
) -> tuple[CandidateValidityRecord, ...]:
    return tuple(c for c in candidates if c.status is ValidityStatus.VALID)
