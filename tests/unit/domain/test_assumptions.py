from __future__ import annotations

import pytest

from fedact.domain.enums import ScientificAssumption, ScientificOutcome
from fedact.domain.records import (
    CHRONOLOGY_CONSEQUENCE,
    CUTOFF_FIXED_REPRESENTATION_CONSEQUENCE,
    AssumptionContractError,
    ContentChecksum,
    CutoffManifest,
    CutoffManifestEntry,
    LaterRealIsolationGate,
    LaterRealReadError,
    LeakageAuditFinding,
    SplitCutoffIdentity,
    assumption_consequence,
    audit_chronology,
    lock_encoder_hash,
    open_later_real_evaluation,
    verify_encoder_hash_lock,
)


def test_every_roadmap_section_six_assumption_is_enumerated() -> None:
    assert {assumption.value for assumption in ScientificAssumption} == {
        "chronology",
        "shared-component",
        "informative-controls",
        "control-span-validity",
        "private-transition-allowance",
        "cutoff-fixed-representation",
        "action-validity",
        "historical-predictability",
        "eigendecomposition-stability",
        "minimum-support",
        "plausibility-set-coverage",
        "honest-primary-federation",
        "operator-coverage",
        "temporal-stability",
    }


def test_chronology_contract_matches_the_roadmap_row_exactly() -> None:
    contract = assumption_consequence(ScientificAssumption.CHRONOLOGY)
    assert contract is CHRONOLOGY_CONSEQUENCE
    assert contract.failure_outcome is ScientificOutcome.ASSUMPTION_VIOLATION
    assert contract.operationalization == "cutoff manifests"
    assert contract.validation == "leakage audit"


def test_cutoff_fixed_representation_contract_matches_the_roadmap_row_exactly() -> None:
    contract = assumption_consequence(ScientificAssumption.CUTOFF_FIXED_REPRESENTATION)
    assert contract is CUTOFF_FIXED_REPRESENTATION_CONSEQUENCE
    assert contract.failure_outcome is ScientificOutcome.ASSUMPTION_VIOLATION
    assert contract.operationalization == "encoder hash lock"
    assert contract.validation == "artifact verification"


def test_assumptions_without_executable_contracts_are_rejected() -> None:
    with pytest.raises(AssumptionContractError):
        assumption_consequence(ScientificAssumption.SHARED_COMPONENT)


def test_cutoff_manifest_requires_source_observable_units() -> None:
    entry = CutoffManifestEntry(
        cutoff_identity=SplitCutoffIdentity("cutoff-2024-01"),
        historical_window_start_month=1,
        cutoff_exclusive_end_month=13,
        source_observable=False,
    )
    with pytest.raises(AssumptionContractError, match="prospective claims are invalid"):
        _ = CutoffManifest(entries=(entry,))


def test_cutoff_manifest_rejects_duplicate_identities() -> None:
    identity = SplitCutoffIdentity("cutoff-2024-01")
    entries = (
        CutoffManifestEntry(identity, 1, 13, True),
        CutoffManifestEntry(identity, 2, 14, True),
    )
    with pytest.raises(AssumptionContractError, match="duplicate cutoff identities"):
        _ = CutoffManifest(entries=entries)


def test_leakage_audit_passes_when_no_future_information_was_used() -> None:
    result = audit_chronology(
        (
            LeakageAuditFinding(
                violating_unit=SplitCutoffIdentity("lamda/cutoff-2023-06"),
                information_available_at_or_after_cutoff=False,
            ),
            LeakageAuditFinding(
                violating_unit=SplitCutoffIdentity("ember2024/cutoff-2024-05"),
                information_available_at_or_after_cutoff=False,
            ),
        )
    )
    assert result.is_passing
    assert result.audited_units == 2


def test_chronology_failure_makes_prospective_claims_invalid() -> None:
    finding = LeakageAuditFinding(
        violating_unit=SplitCutoffIdentity("lamda/cutoff-2023-06"),
        information_available_at_or_after_cutoff=True,
    )
    with pytest.raises(AssumptionContractError, match="prospective claims are invalid"):
        audit_chronology((finding,))
    assert CHRONOLOGY_CONSEQUENCE.failure_outcome is ScientificOutcome.ASSUMPTION_VIOLATION


def test_encoder_hash_lock_requires_at_least_one_locked_boundary() -> None:
    checksum = ContentChecksum("sha256:abc")
    with pytest.raises(AssumptionContractError):
        lock_encoder_hash(checksum, ())


def test_encoder_hash_lock_verification_passes_for_matching_checkpoint() -> None:
    locked = lock_encoder_hash(
        ContentChecksum("sha256:abc"),
        ("nuisance", "transition", "calibration", "hardening", "later-real"),
    )
    verify_encoder_hash_lock(locked, ContentChecksum("sha256:abc"))


def test_encoder_hash_change_invalidates_mechanistic_attribution() -> None:
    locked = lock_encoder_hash(ContentChecksum("sha256:abc"), ("nuisance",))
    different = ContentChecksum("sha256:different")
    with pytest.raises(AssumptionContractError, match="mechanistic attribution is invalid"):
        verify_encoder_hash_lock(locked, different)
    assert CUTOFF_FIXED_REPRESENTATION_CONSEQUENCE.failure_outcome is (
        ScientificOutcome.ASSUMPTION_VIOLATION
    )


def test_later_real_observations_stay_sealed_until_inputs_complete() -> None:
    gate = LaterRealIsolationGate(
        cutoff_identity=SplitCutoffIdentity("month-000024"),
        required_scientific_inputs_complete=False,
    )
    with pytest.raises(LaterRealReadError, match="evaluation-only"):
        open_later_real_evaluation(gate)


def test_completed_scientific_inputs_open_later_real_evaluation() -> None:
    gate = LaterRealIsolationGate(
        cutoff_identity=SplitCutoffIdentity("month-000024"),
        required_scientific_inputs_complete=True,
    )
    open_later_real_evaluation(gate)
