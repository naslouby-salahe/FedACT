from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import combinations
from typing import NewType, Protocol, cast

import lief
import numpy as np
import pefile
import torch

from fedact.data.ember2024 import (
    APK_PAYLOAD_SIZES,
    PE_PAYLOAD_SIZES,
    PayloadBytes,
    PeFileBytes,
    PeImportName,
    PeSectionRenameTarget,
    UpxAction,
    add_entry_point_trampoline,
    add_read_only_section,
    add_unused_import,
    append_benign_eof_bytes,
    apply_upx_action,
    fill_existing_section_slack,
    remove_authenticode_directory,
    remove_debug_directory,
    rename_section,
    zero_pe_checksum,
)
from fedact.domain.records import AssumptionConsequence
from fedact.domain.types import (
    ActionCount,
    AmbiguityFlag,
    CertificationFlag,
    CoordinateValue,
    DatasetName,
    DomainValidityFlag,
    FamilyName,
    HashDigest,
    IntervalBound,
    MetricRate,
    NormalizedOperatorFormText,
    NormValue,
    OperatorIdentifier,
    OrderIndex,
    ProvenanceText,
    RuleDescription,
    SampleCount,
    SampleIdentifier,
    ScientificAssumption,
    ScientificOutcome,
    SimilarityScore,
    SplitCutoffIdentity,
    SufficiencyFlag,
    ThresholdValue,
    TimeoutSeconds,
    ToolchainIdentifier,
    UsageCount,
    ValidationFlag,
)


class NumericalFailureError(RuntimeError):
    pass


@dataclass(frozen=True)
class ActionInterval:
    lower: IntervalBound
    upper: IntervalBound

    def __post_init__(self) -> None:
        if self.lower > self.upper:
            raise NumericalFailureError(
                f"Inverted interval: lower ({self.lower}) > upper ({self.upper})"
            )

    @property
    def width(self) -> IntervalBound:
        return self.upper - self.lower

    def is_certified_positive(
        self, threshold: ThresholdValue, ambiguity_width: ThresholdValue
    ) -> CertificationFlag:
        return self.lower >= threshold and self.width <= ambiguity_width

    def is_certified_negative(
        self, threshold: ThresholdValue, ambiguity_width: ThresholdValue
    ) -> CertificationFlag:
        return self.upper < threshold and self.width <= ambiguity_width

    def is_ambiguous(
        self, threshold: ThresholdValue, ambiguity_width: ThresholdValue
    ) -> AmbiguityFlag:
        return self.lower < threshold <= self.upper or self.width > ambiguity_width


def projector_from_basis(basis: np.ndarray | torch.Tensor) -> np.ndarray:
    b = np.array(basis) if isinstance(basis, torch.Tensor) else basis
    d = b.shape[0]
    if b.size == 0 or b.shape[1] == 0:
        return np.eye(d)
    q, _unused = np.linalg.qr(b)
    return np.eye(d) - q @ q.T


def support_interval(
    direction: np.ndarray | torch.Tensor,
    vertices: Sequence[np.ndarray | torch.Tensor],
) -> ActionInterval:
    if not vertices:
        return ActionInterval(lower=0.0, upper=0.0)
    d = np.array(direction) if isinstance(direction, torch.Tensor) else direction
    values = [float(np.dot(d, np.array(v) if isinstance(v, torch.Tensor) else v)) for v in vertices]
    return ActionInterval(lower=min(values), upper=max(values))


def smallest_positive_eigenvalue(
    matrix: np.ndarray | torch.Tensor,
    tolerance: ThresholdValue,
    rank_epsilon_relative: ThresholdValue,
) -> CoordinateValue | None:
    m = np.array(matrix) if isinstance(matrix, torch.Tensor) else matrix
    eigs = np.linalg.eigvalsh(m)
    max_eig = float(np.max(eigs)) if eigs.size > 0 else 0.0
    if max_eig < tolerance:
        return None
    cutoff = max(1e-12, float(max_eig * rank_epsilon_relative))
    pos = [float(ev) for ev in eigs if ev > cutoff]
    return min(pos) if pos else None


def action_conditioning_index(
    action: np.ndarray | torch.Tensor,
    information_matrix: np.ndarray | torch.Tensor,
) -> CoordinateValue | None:
    a = np.array(action) if isinstance(action, torch.Tensor) else action
    norm = float(np.linalg.norm(a))
    if norm < 1e-12:
        return None
    u = a / norm
    h = (
        np.array(information_matrix)
        if isinstance(information_matrix, torch.Tensor)
        else information_matrix
    )
    return float(u.T @ h @ u)


@dataclass(frozen=True)
class ActionDisplacementResult:
    displacement_vector: torch.Tensor | np.ndarray
    displacement_norm: NormValue
    rejected_as_degenerate: ValidationFlag


def evaluate_displacement(
    source: np.ndarray | torch.Tensor,
    target: np.ndarray | torch.Tensor,
    zero_displacement_floor: ThresholdValue,
) -> ActionDisplacementResult:
    s = np.array(source) if isinstance(source, torch.Tensor) else source
    t = np.array(target) if isinstance(target, torch.Tensor) else target
    delta = t - s
    norm = float(np.linalg.norm(delta))
    degen = norm < zero_displacement_floor
    return ActionDisplacementResult(
        displacement_vector=delta,
        displacement_norm=norm,
        rejected_as_degenerate=degen,
    )


def action_support_bounds(
    direction: np.ndarray | torch.Tensor,
    vertices: Sequence[np.ndarray | torch.Tensor],
) -> ActionInterval:
    return support_interval(direction, vertices)


def box_diameter_bound(
    lowers: Sequence[IntervalBound],
    uppers: Sequence[IntervalBound],
) -> IntervalBound:
    diffs = [u_val - l_val for l_val, u_val in zip(lowers, uppers, strict=True)]
    return float(np.sqrt(sum(d * d for d in diffs)))


OperatorName = NewType("OperatorName", str)
NormalizedParameterString = NewType("NormalizedParameterString", str)
OutputHash = NewType("OutputHash", str)
CoverageRatio = NewType("CoverageRatio", float)
CompositionLengthLimit = NewType("CompositionLengthLimit", int)


class OperatorDomain(StrEnum):
    WINDOWS_PE = "windows-pe"
    ANDROID_APK = "android-apk"


@dataclass(frozen=True)
class OperatorFamily:
    name: FamilyName
    domain: OperatorDomain
    listed_order: OrderIndex
    parameter_grid: tuple[NormalizedParameterString, ...]


@dataclass(frozen=True)
class OperatorRecord:
    operator_name: OperatorName
    dataset: DatasetName
    domain: OperatorDomain
    semantic_validity_contract: RuleDescription
    construction_function: RuleDescription
    parameter_domain: tuple[NormalizedParameterString, ...]
    eligibility_rule: RuleDescription
    rejection_rule: RuleDescription
    representation_displacement_rule: RuleDescription
    zero_displacement_rule: RuleDescription
    maximum_uses_per_sample: UsageCount
    provenance: ProvenanceText


@dataclass(frozen=True)
class OperatorComposition:
    families: tuple[OperatorFamily, ...]
    parameters: tuple[NormalizedParameterString, ...]

    def __post_init__(self) -> None:
        family_names = [family.name for family in self.families]
        if len(set(family_names)) != len(family_names):
            raise ValueError("an operator composition may not repeat an atomic family")
        if len(self.families) != len(self.parameters):
            raise ValueError("composition families and parameters must align")
        if not self.families:
            raise ValueError("an operator composition must contain at least one atomic action")


@dataclass(frozen=True)
class OperatorCandidate:
    composition: OperatorComposition
    normalized_form: NormalizedOperatorFormText
    source_sample_id: SampleIdentifier
    cutoff_identity: SplitCutoffIdentity


@dataclass(frozen=True)
class ActionDisplacement:
    candidate: OperatorCandidate
    displacement_norm: NormValue


@dataclass(frozen=True)
class ZeroDisplacementRejection:
    candidate: OperatorCandidate
    observed_norm: NormValue
    floor: ThresholdValue

    def __post_init__(self) -> None:
        if self.observed_norm >= self.floor:
            raise ValueError(
                "zero-displacement rejection requires a norm below the configured floor"
            )


class EnumerationContractError(ValueError):
    pass


def _normalized_form(
    families: tuple[OperatorFamily, ...], parameters: tuple[NormalizedParameterString, ...]
) -> NormalizedOperatorFormText:
    pairs = zip(families, parameters, strict=True)
    parts = [f"{family.name}={parameter}" for family, parameter in pairs]
    return "|".join(parts)


def _ordered_composition(
    families: tuple[OperatorFamily, ...], parameters: tuple[NormalizedParameterString, ...]
) -> OperatorComposition:
    paired = sorted(zip(families, parameters, strict=True), key=lambda pair: pair[0].listed_order)
    ordered_families = tuple(family for family, _unused in paired)
    ordered_parameters = tuple(parameter for _unused, parameter in paired)
    return OperatorComposition(families=ordered_families, parameters=ordered_parameters)


def _compositions_of_length(
    selections: tuple[tuple[OperatorFamily, NormalizedParameterString], ...],
    length: ActionCount,
) -> list[OperatorComposition]:
    compositions: list[OperatorComposition] = []
    for chosen in combinations(selections, length):
        chosen_families = tuple(family for family, _unused in chosen)
        names = [family.name for family in chosen_families]
        if len(set(names)) != len(names):
            continue
        parameters = tuple(parameter for _unused, parameter in chosen)
        compositions.append(_ordered_composition(chosen_families, parameters))
    return compositions


def enumerate_candidates(
    families: tuple[OperatorFamily, ...],
    maximum_composed_atomic_actions: CompositionLengthLimit,
    source_sample_id: SampleIdentifier,
    cutoff_identity: SplitCutoffIdentity,
) -> tuple[OperatorCandidate, ...]:
    if maximum_composed_atomic_actions < 1:
        raise EnumerationContractError("maximum composed atomic actions must be at least one")
    ordered_families = tuple(sorted(families, key=lambda family: family.listed_order))
    listed_orders = [family.listed_order for family in ordered_families]
    if len(set(listed_orders)) != len(listed_orders):
        raise EnumerationContractError("operator families must have unique listed orders")
    selections: list[tuple[OperatorFamily, NormalizedParameterString]] = []
    for family in ordered_families:
        for parameter in sorted(family.parameter_grid):
            selections.append((family, parameter))

    candidates: list[OperatorCandidate] = []
    seen: set[str] = set()
    for length in range(1, maximum_composed_atomic_actions + 1):
        for composition in _compositions_of_length(tuple(selections), length):
            normalized_form = _normalized_form(composition.families, composition.parameters)
            if normalized_form in seen:
                continue
            seen.add(normalized_form)
            candidates.append(
                OperatorCandidate(
                    composition=composition,
                    normalized_form=normalized_form,
                    source_sample_id=source_sample_id,
                    cutoff_identity=cutoff_identity,
                )
            )
    return tuple(candidates)


class OperatorCoverageError(ValueError):
    pass


ACTION_VALIDITY_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.ACTION_VALIDITY,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="operator-specific validator",
    validation="validity audit",
)

OPERATOR_COVERAGE_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.OPERATOR_COVERAGE,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="operator coverage audit",
    validation="later-real coverage diagnostics",
)


@dataclass(frozen=True)
class ValidityAuditEntry:
    operator_name: OperatorIdentifier
    domain: OperatorDomain
    cutoff_identity: SplitCutoffIdentity
    structural_valid: ValidationFlag
    execution_valid: ValidationFlag
    maliciousness_preserved: ValidationFlag
    behavior_preserved: ValidationFlag

    def is_domain_valid(self) -> DomainValidityFlag:
        return (
            self.structural_valid
            and self.execution_valid
            and self.maliciousness_preserved
            and self.behavior_preserved
        )


def run_validity_audit(entries: tuple[ValidityAuditEntry, ...]) -> tuple[ValidityAuditEntry, ...]:
    invalid = [entry for entry in entries if not entry.is_domain_valid()]
    if any(not entry.is_domain_valid() for entry in entries):
        raise OperatorCoverageError(
            "action validity violated; certified transformations are unusable for: "
            f"{[entry.operator_name for entry in invalid]}"
        )
    return tuple(entries)


@dataclass(frozen=True)
class OperatorCoverageAudit:
    cutoff_identity: SplitCutoffIdentity
    operator_eligible_source_samples: SampleCount
    samples_with_valid_nondegenerate_candidate: SampleCount
    minimum_valid_coverage: MetricRate

    @property
    def observed_coverage(self) -> CoverageRatio | None:
        denominator = self.operator_eligible_source_samples
        if denominator == 0:
            return None
        return CoverageRatio(self.samples_with_valid_nondegenerate_candidate / denominator)

    def is_coverage_sufficient(self) -> SufficiencyFlag:
        coverage = self.observed_coverage
        if coverage is None:
            raise OperatorCoverageError(
                "operator-dependent execution must emit ABSTAIN_OPERATOR_COVERAGE_INSUFFICIENT "
                "when the operator-eligible denominator is zero"
            )
        return coverage >= self.minimum_valid_coverage


class ValidityStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"


class ValidityLayerError(ValueError):
    pass


@dataclass(frozen=True)
class StructuralValidity:
    parser_primary_ok: ValidationFlag
    parser_secondary_ok: ValidationFlag
    expected_machine_type: ValidationFlag

    @property
    def is_valid(self) -> DomainValidityFlag:
        return self.parser_primary_ok and self.parser_secondary_ok and self.expected_machine_type


@dataclass(frozen=True)
class ExecutionSmokeValidity:
    source_launched: ValidationFlag
    transformed_launched: ValidationFlag
    no_new_crash_or_anr: ValidationFlag
    sandbox_identity_recorded: ValidationFlag
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


BENIGN_GADGET_LIBRARY = "cutoff-safe-benign-gadget-library"


def lamda_families() -> tuple[OperatorFamily, ...]:
    return (
        OperatorFamily(
            name="unreachable-benign-gadget-injection",
            domain=OperatorDomain.ANDROID_APK,
            listed_order=0,
            parameter_grid=(NormalizedParameterString(f"gadget-library={BENIGN_GADGET_LIBRARY}"),),
        ),
        OperatorFamily(
            name="permission-neutral-resource-injection",
            domain=OperatorDomain.ANDROID_APK,
            listed_order=1,
            parameter_grid=tuple(
                NormalizedParameterString(f"payload={size}") for size in sorted(APK_PAYLOAD_SIZES)
            ),
        ),
    )


GadgetLibraryIdentity = NewType("GadgetLibraryIdentity", str)


def pe_operator_enumerations() -> tuple[
    type[PeImportName], type[PeSectionRenameTarget], type[UpxAction]
]:
    return (PeImportName, PeSectionRenameTarget, UpxAction)


def gadget_library_identity() -> GadgetLibraryIdentity:
    return GadgetLibraryIdentity(BENIGN_GADGET_LIBRARY)


_ = PayloadBytes


def pe_mutation_families() -> tuple[OperatorFamily, ...]:
    return (
        OperatorFamily(
            name="append-benign-eof-bytes",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=0,
            parameter_grid=tuple(
                NormalizedParameterString(f"payload={size}") for size in sorted(PE_PAYLOAD_SIZES)
            ),
        ),
        OperatorFamily(
            name="fill-existing-section-slack",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=1,
            parameter_grid=tuple(
                NormalizedParameterString(f"payload={size} (truncated to available slack)")
                for size in sorted(PE_PAYLOAD_SIZES)
            ),
        ),
        OperatorFamily(
            name="add-unused-import",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=2,
            parameter_grid=tuple(
                NormalizedParameterString(f"import={name}") for name in sorted(PeImportName)
            ),
        ),
        OperatorFamily(
            name="rename-section",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=3,
            parameter_grid=tuple(
                NormalizedParameterString(f"section={item}")
                for item in sorted(PeSectionRenameTarget)
            ),
        ),
        OperatorFamily(
            name="add-read-only-section",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=4,
            parameter_grid=tuple(
                NormalizedParameterString(f"payload={size}")
                for size in sorted(PE_PAYLOAD_SIZES)
                if size != PayloadBytes(64)
            ),
        ),
        OperatorFamily(
            name="entry-point-trampoline",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=5,
            parameter_grid=(NormalizedParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name="remove-authenticode-directory",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=6,
            parameter_grid=(NormalizedParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name="zero-pe-checksum",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=7,
            parameter_grid=(NormalizedParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name="remove-debug-directory",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=8,
            parameter_grid=(NormalizedParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name="upx-pack-unpack",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=9,
            parameter_grid=tuple(
                NormalizedParameterString(f"action={item}") for item in sorted(UpxAction)
            ),
        ),
    )


_PEFILE_FILE_HEADER_MACHINE_ATTRIBUTE = "Machine"
_PEFILE_MACHINE_TYPES = cast("dict[str, int]", pefile.MACHINE_TYPE)
_EXPECTED_PE_MACHINE_TYPES: frozenset[int] = frozenset(
    {
        _PEFILE_MACHINE_TYPES["IMAGE_FILE_MACHINE_I386"],
        _PEFILE_MACHINE_TYPES["IMAGE_FILE_MACHINE_AMD64"],
    }
)


class UnsupportedOperatorFamilyError(ValueError):
    pass


class MutationStructuralIntegrityError(ValueError):
    pass


PeMachineCode = NewType("PeMachineCode", int)


class PeFileHeader(Protocol):
    Machine: PeMachineCode


def _parameter_value(parameter: NormalizedParameterString) -> NormalizedParameterString:
    if "=" not in parameter:
        return parameter
    return NormalizedParameterString(parameter.split("=", 1)[1].split(" ", 1)[0])


def apply_pe_operator_family(
    family: OperatorFamily, parameter: NormalizedParameterString, pe_bytes: PeFileBytes
) -> PeFileBytes:
    value = _parameter_value(parameter)
    if family.name == "append-benign-eof-bytes":
        return append_benign_eof_bytes(pe_bytes, PayloadBytes(int(value)))
    if family.name == "fill-existing-section-slack":
        return fill_existing_section_slack(pe_bytes, PayloadBytes(int(value)))
    if family.name == "add-unused-import":
        return add_unused_import(pe_bytes, PeImportName(value))
    if family.name == "rename-section":
        return rename_section(pe_bytes, PeSectionRenameTarget(value))
    if family.name == "add-read-only-section":
        return add_read_only_section(pe_bytes, PayloadBytes(int(value)))
    if family.name == "entry-point-trampoline":
        return add_entry_point_trampoline(pe_bytes)
    if family.name == "remove-authenticode-directory":
        return remove_authenticode_directory(pe_bytes)
    if family.name == "zero-pe-checksum":
        return zero_pe_checksum(pe_bytes)
    if family.name == "remove-debug-directory":
        return remove_debug_directory(pe_bytes)
    if family.name == "upx-pack-unpack":
        return apply_upx_action(pe_bytes, UpxAction(value))
    raise UnsupportedOperatorFamilyError(f"unsupported PE operator family: {family.name}")


def structural_validity_of(pe_bytes: PeFileBytes) -> StructuralValidity:
    parser_primary_ok = lief.PE.parse(list(pe_bytes)) is not None
    try:
        secondary = pefile.PE(data=bytes(pe_bytes), fast_load=True)
        parser_secondary_ok = True
        file_header = cast(PeFileHeader, secondary.FILE_HEADER)
        machine_type = file_header.Machine
        expected_machine_type = machine_type in _EXPECTED_PE_MACHINE_TYPES
    except pefile.PEFormatError:
        parser_secondary_ok = False
        expected_machine_type = False
    return StructuralValidity(
        parser_primary_ok=parser_primary_ok,
        parser_secondary_ok=parser_secondary_ok,
        expected_machine_type=expected_machine_type,
    )


def structural_validity_status(pe_bytes: PeFileBytes) -> ValidityStatus:
    if structural_validity_of(pe_bytes).is_valid:
        return ValidityStatus.VALID
    return ValidityStatus.INVALID


def apply_and_verify_pe_operator_family(
    family: OperatorFamily, parameter: NormalizedParameterString, pe_bytes: PeFileBytes
) -> PeFileBytes:
    mutated = apply_pe_operator_family(family, parameter, pe_bytes)
    if structural_validity_status(mutated) is ValidityStatus.INVALID:
        raise MutationStructuralIntegrityError(
            f"mutation family {family.name!r} produced a structurally invalid PE file"
        )
    return mutated
