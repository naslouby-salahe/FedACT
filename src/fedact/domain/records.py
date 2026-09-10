from __future__ import annotations

from dataclasses import dataclass

from fedact.domain.types import (
    ArtifactBoundary,
    ArtifactName,
    ContentChecksum,
    DependencyFingerprint,
    DetailMessage,
    MonthIndex,
    OperationalizationText,
    PassingFlag,
    ScientificAssumption,
    ScientificOutcome,
    SplitCutoffIdentity,
    UnitCount,
    ValidationFlag,
)


class AssumptionContractError(ValueError):
    pass


@dataclass(frozen=True)
class AssumptionConsequence:
    assumption: ScientificAssumption
    failure_outcome: ScientificOutcome
    operationalization: OperationalizationText
    validation: DetailMessage


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
    historical_window_start_month: MonthIndex
    cutoff_exclusive_end_month: MonthIndex
    source_observable: ValidationFlag


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
    information_available_at_or_after_cutoff: ValidationFlag


@dataclass(frozen=True)
class LeakageAuditResult:
    audited_units: UnitCount
    findings: tuple[LeakageAuditFinding, ...]

    @property
    def is_passing(self) -> PassingFlag:
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
    locked_for_boundaries: frozenset[ArtifactName]


def lock_encoder_hash(
    representation_checkpoint_hash: ContentChecksum,
    locked_for_boundaries: tuple[ArtifactName, ...],
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


class LaterRealReadError(ValueError):
    pass


@dataclass(frozen=True)
class LaterRealIsolationGate:
    cutoff_identity: SplitCutoffIdentity
    required_scientific_inputs_complete: ValidationFlag


def open_later_real_evaluation(gate: LaterRealIsolationGate) -> None:
    if not gate.required_scientific_inputs_complete:
        raise LaterRealReadError(
            f"later-real observations for {gate.cutoff_identity} may be read only by "
            "evaluation producers after all corresponding scientific inputs and decision "
            "artifacts have reached COMPLETE; later-real data are evaluation-only"
        )


@dataclass(frozen=True)
class BoundaryFingerprint:
    boundary: ArtifactBoundary
    dependency_fingerprint: DependencyFingerprint


@dataclass(frozen=True)
class BoundaryFingerprints:
    entries: tuple[BoundaryFingerprint, ...] = ()

    def __bool__(self) -> bool:
        return bool(self.entries)

    def for_boundary(self, boundary: ArtifactBoundary) -> DependencyFingerprint | None:
        for entry in self.entries:
            if entry.boundary is boundary:
                return entry.dependency_fingerprint
        return None


SHARED_COMPONENT_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.SHARED_COMPONENT,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="cross-client feasibility and stability",
    validation="local-vs-global diagnostics",
)

INFORMATIVE_CONTROLS_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.INFORMATIVE_CONTROLS,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="matched control strata",
    validation="held-out control reconstruction",
)

CONTROL_SPAN_VALIDITY_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.CONTROL_SPAN_VALIDITY,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="calibrated/sensitivity radius",
    validation="violation sweeps",
)

PRIVATE_TRANSITION_ALLOWANCE_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.PRIVATE_TRANSITION_ALLOWANCE,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="calibrated/sensitivity allowance",
    validation="private-transition sweep",
)

HISTORICAL_PREDICTABILITY_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.HISTORICAL_PREDICTABILITY,
    failure_outcome=ScientificOutcome.INSUFFICIENT_EVIDENCE,
    operationalization="nested pseudo-future calibration",
    validation="time shuffle and pseudo-future coverage",
)

EIGENDECOMPOSITION_STABILITY_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.EIGENDECOMPOSITION_STABILITY,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="minimum eigengap criterion",
    validation="bootstrap/stability diagnostic",
)

MINIMUM_SUPPORT_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.MINIMUM_SUPPORT,
    failure_outcome=ScientificOutcome.INSUFFICIENT_EVIDENCE,
    operationalization="minimum-support gate",
    validation="support counts",
)

PLAUSIBILITY_SET_COVERAGE_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.PLAUSIBILITY_SET_COVERAGE,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="pre-cutoff calibration",
    validation="radius sensitivity",
)

HONEST_PRIMARY_FEDERATION_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.HONEST_PRIMARY_FEDERATION,
    failure_outcome=ScientificOutcome.FAIL,
    operationalization="authenticated-client-summaries",
    validation="outlier stress tests only",
)

TEMPORAL_STABILITY_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.TEMPORAL_STABILITY,
    failure_outcome=ScientificOutcome.ABSTENTION_EXPECTED,
    operationalization="nested pseudo-future validation",
    validation="horizon calibration",
)

EXTENDED_ASSUMPTION_CONTRACTS: tuple[AssumptionConsequence, ...] = (
    SHARED_COMPONENT_CONSEQUENCE,
    INFORMATIVE_CONTROLS_CONSEQUENCE,
    CONTROL_SPAN_VALIDITY_CONSEQUENCE,
    PRIVATE_TRANSITION_ALLOWANCE_CONSEQUENCE,
    HISTORICAL_PREDICTABILITY_CONSEQUENCE,
    EIGENDECOMPOSITION_STABILITY_CONSEQUENCE,
    MINIMUM_SUPPORT_CONSEQUENCE,
    PLAUSIBILITY_SET_COVERAGE_CONSEQUENCE,
    HONEST_PRIMARY_FEDERATION_CONSEQUENCE,
    TEMPORAL_STABILITY_CONSEQUENCE,
)


FEDACT_ASSUMPTION_CONTRACTS: dict[ScientificAssumption, AssumptionConsequence] = {
    consequence.assumption: consequence for consequence in EXTENDED_ASSUMPTION_CONTRACTS
}
