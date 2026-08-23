from __future__ import annotations

from dataclasses import dataclass

from fedact.domain.enums import ScientificAssumption, ScientificOutcome
from fedact.domain.records import ContentChecksum, SplitCutoffIdentity


class AssumptionContractError(ValueError):
    pass


@dataclass(frozen=True)
class AssumptionConsequence:
    assumption: ScientificAssumption
    failure_outcome: ScientificOutcome
    operationalization: str
    validation: str


CHRONOLOGY_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.CHRONOLOGY,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="cutoff manifests",
    validation="leakage audit",
)

CUTOFF_FIXED_REPRESENTATION_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.CUTOFF_FIXED_REPRESENTATION,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="encoder hash lock",
    validation="artifact verification",
)

ASSUMPTION_CONTRACTS: dict[ScientificAssumption, AssumptionConsequence] = {
    consequence.assumption: consequence
    for consequence in (
        CHRONOLOGY_CONSEQUENCE,
        CUTOFF_FIXED_REPRESENTATION_CONSEQUENCE,
    )
}


def assumption_consequence(assumption: ScientificAssumption) -> AssumptionConsequence:
    contract = ASSUMPTION_CONTRACTS.get(assumption)
    if contract is None:
        raise AssumptionContractError(
            f"no executable failure contract is registered for assumption {assumption}"
        )
    return contract


@dataclass(frozen=True)
class CutoffManifestEntry:
    cutoff_identity: SplitCutoffIdentity
    historical_window_start_month: int
    cutoff_exclusive_end_month: int
    source_observable: bool


@dataclass(frozen=True)
class CutoffManifest:
    entries: tuple[CutoffManifestEntry, ...]

    def __post_init__(self) -> None:
        identities = [entry.cutoff_identity for entry in self.entries]
        if len(set(identities)) != len(identities):
            raise AssumptionContractError("cutoff manifest contains duplicate cutoff identities")
        unobservable = [
            entry.cutoff_identity for entry in self.entries if not entry.source_observable
        ]
        if unobservable:
            raise AssumptionContractError(
                f"cutoff manifest contains non-source-observable cutoffs: {unobservable}; "
                "prospective claims are invalid for these units"
            )


@dataclass(frozen=True)
class LeakageAuditFinding:
    violating_unit: SplitCutoffIdentity
    information_available_at_or_after_cutoff: bool


@dataclass(frozen=True)
class LeakageAuditResult:
    audited_units: int
    findings: tuple[LeakageAuditFinding, ...]

    @property
    def is_passing(self) -> bool:
        return not any(
            finding.information_available_at_or_after_cutoff for finding in self.findings
        )


def audit_chronology(findings: tuple[LeakageAuditFinding, ...]) -> LeakageAuditResult:
    result = LeakageAuditResult(audited_units=len(findings), findings=findings)
    violations = [
        finding for finding in findings if finding.information_available_at_or_after_cutoff
    ]
    if violations:
        raise AssumptionContractError(
            "chronology leakage audit failed; prospective claims are invalid for units: "
            f"{[finding.violating_unit for finding in violations]}"
        )
    return result


@dataclass(frozen=True)
class EncoderHashLock:
    representation_checkpoint_hash: ContentChecksum
    locked_for_boundaries: frozenset[str]


def lock_encoder_hash(
    representation_checkpoint_hash: ContentChecksum, locked_for_boundaries: tuple[str, ...]
) -> EncoderHashLock:
    if not locked_for_boundaries:
        raise AssumptionContractError(
            "the encoder hash lock must name at least one downstream scientific boundary"
        )
    return EncoderHashLock(
        representation_checkpoint_hash=representation_checkpoint_hash,
        locked_for_boundaries=frozenset(locked_for_boundaries),
    )


def verify_encoder_hash_lock(
    lock: EncoderHashLock, observed_checkpoint_hash: ContentChecksum
) -> None:
    if lock.representation_checkpoint_hash != observed_checkpoint_hash:
        raise AssumptionContractError(
            "cutoff-fixed representation verification failed: the observed encoder hash "
            f"{observed_checkpoint_hash} does not match the locked hash "
            f"{lock.representation_checkpoint_hash}; mechanistic attribution is invalid"
        )
