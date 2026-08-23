from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fedact.domain.operators.contracts import OperatorCandidate, OutputHash
from fedact.domain.records import SplitCutoffIdentity


class ValidityStatus(StrEnum):
    VALID = "VALID"
    REJECT = "REJECT"
    MALICIOUSNESS_VALIDATION_UNAVAILABLE = "MALICIOUSNESS_VALIDATION_UNAVAILABLE"


class ValidityLayerError(ValueError):
    pass


@dataclass(frozen=True)
class StructuralValidity:
    parser_primary_ok: bool
    parser_secondary_ok: bool
    expected_machine_type: bool

    def is_valid(self) -> bool:
        return self.parser_primary_ok and self.parser_secondary_ok and self.expected_machine_type


@dataclass(frozen=True)
class ExecutionSmokeValidity:
    source_launched: bool
    transformed_launched: bool
    no_new_crash_or_anr: bool
    sandbox_identity_recorded: bool
    within_timeout_seconds: float

    def is_valid(self) -> bool:
        return (
            self.source_launched
            and self.transformed_launched
            and self.no_new_crash_or_anr
            and self.sandbox_identity_recorded
        )


@dataclass(frozen=True)
class MaliciousnessValidity:
    source_detected: bool
    transformed_detected: bool

    @property
    def is_unavailable(self) -> bool:
        return not self.source_detected

    def is_valid(self) -> bool:
        return self.source_detected and self.transformed_detected


@dataclass(frozen=True)
class BehaviorValidity:
    jaccard_similarity: float
    minimum_behavior_jaccard: float
    both_event_sets_empty: bool

    def is_valid(self) -> bool:
        if self.both_event_sets_empty:
            return False
        return self.jaccard_similarity >= self.minimum_behavior_jaccard


@dataclass(frozen=True)
class CandidateValidityRecord:
    candidate: OperatorCandidate
    structural: StructuralValidity
    execution: ExecutionSmokeValidity
    maliciousness: MaliciousnessValidity
    behavior: BehaviorValidity
    toolchain_identity: str
    source_hash: str
    output_hash: OutputHash | None
    cutoff_identity: SplitCutoffIdentity

    def validity_status(self) -> ValidityStatus:
        if self.maliciousness.is_unavailable:
            return ValidityStatus.MALICIOUSNESS_VALIDATION_UNAVAILABLE
        if not (
            self.structural.is_valid()
            and self.execution.is_valid()
            and self.maliciousness.is_valid()
            and self.behavior.is_valid()
        ):
            return ValidityStatus.REJECT
        return ValidityStatus.VALID


def require_all_four_layers(record: CandidateValidityRecord) -> None:
    status = record.validity_status()
    if status is not ValidityStatus.VALID:
        raise ValidityLayerError(
            f"candidate {record.candidate.canonical_form} is not confirmatory evidence: {status}"
        )
