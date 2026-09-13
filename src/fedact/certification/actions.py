from __future__ import annotations

import re
import subprocess
import tempfile
import time
from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from itertools import combinations
from pathlib import Path
from typing import Protocol, cast

import lief
import numpy as np
import pefile
import torch
from androguard.core.apk import APK

from fedact.data.ember2024 import (
    APK_PAYLOAD_SIZES,
    PE_PAYLOAD_SIZES,
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
from fedact.data.lamda_apk_emulator import (
    EmulatorHandle,
    jaccard_similarity,
    run_dynamic_smoke,
)
from fedact.data.lamda_apk_mutations import (
    ApkSigningIdentity,
    apply_apk_operator_family,
)
from fedact.domain.records import AssumptionConsequence
from fedact.domain.types import (
    ActionCount,
    AmbiguityFlag,
    AndroidPackageName,
    ApkFileBytes,
    ApkOperatorFamilyName,
    CertificationFlag,
    CompositionLengthLimit,
    CoordinateValue,
    CoverageRatio,
    DomainValidityFlag,
    FileSuffix,
    HashDigest,
    IntervalBound,
    MetricRate,
    MonkeyEventCount,
    NormalizedOperatorFormText,
    NormalizedParameterString,
    NormValue,
    OperatorFamilyName,
    OperatorIdentifier,
    OrderIndex,
    PayloadBytes,
    PeFileBytes,
    PeMachineCode,
    PeOperatorFamilyName,
    RawPayloadBytes,
    SampleCount,
    SampleIdentifier,
    ScientificAssumption,
    ScientificOutcome,
    SeedValue,
    SimilarityScore,
    SplitCutoffIdentity,
    SufficiencyFlag,
    ThresholdValue,
    TimeoutSeconds,
    ToolchainComponent,
    ToolchainIdentifier,
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


class OperatorDomain(StrEnum):
    WINDOWS_PE = "windows-pe"
    ANDROID_APK = "android-apk"


@dataclass(frozen=True)
class OperatorFamily[FamilyNameT: OperatorFamilyName]:
    name: FamilyNameT
    domain: OperatorDomain
    listed_order: OrderIndex
    parameter_grid: tuple[NormalizedParameterString, ...]


type PeOperatorFamily = OperatorFamily[PeOperatorFamilyName]
type ApkOperatorFamily = OperatorFamily[ApkOperatorFamilyName]


@dataclass(frozen=True)
class OperatorComposition[FamilyNameT: OperatorFamilyName]:
    families: tuple[OperatorFamily[FamilyNameT], ...]
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
class OperatorCandidate[FamilyNameT: OperatorFamilyName]:
    composition: OperatorComposition[FamilyNameT]
    normalized_form: NormalizedOperatorFormText
    source_sample_id: SampleIdentifier
    cutoff_identity: SplitCutoffIdentity


@dataclass(frozen=True)
class ActionDisplacement[FamilyNameT: OperatorFamilyName]:
    candidate: OperatorCandidate[FamilyNameT]
    displacement_norm: NormValue


@dataclass(frozen=True)
class ZeroDisplacementRejection[FamilyNameT: OperatorFamilyName]:
    candidate: OperatorCandidate[FamilyNameT]
    observed_norm: NormValue
    floor: ThresholdValue

    def __post_init__(self) -> None:
        if self.observed_norm >= self.floor:
            raise ValueError(
                "zero-displacement rejection requires a norm below the configured floor"
            )


class EnumerationContractError(ValueError):
    pass


def _normalized_form[FamilyNameT: OperatorFamilyName](
    families: tuple[OperatorFamily[FamilyNameT], ...],
    parameters: tuple[NormalizedParameterString, ...],
) -> NormalizedOperatorFormText:
    pairs = zip(families, parameters, strict=True)
    parts = [f"{family.name}={parameter}" for family, parameter in pairs]
    return "|".join(parts)


def _ordered_composition[FamilyNameT: OperatorFamilyName](
    families: tuple[OperatorFamily[FamilyNameT], ...],
    parameters: tuple[NormalizedParameterString, ...],
) -> OperatorComposition[FamilyNameT]:
    paired = sorted(zip(families, parameters, strict=True), key=lambda pair: pair[0].listed_order)
    ordered_families = tuple(family for family, _unused in paired)
    ordered_parameters = tuple(parameter for _unused, parameter in paired)
    return OperatorComposition(families=ordered_families, parameters=ordered_parameters)


def _compositions_of_length[FamilyNameT: OperatorFamilyName](
    selections: tuple[tuple[OperatorFamily[FamilyNameT], NormalizedParameterString], ...],
    length: ActionCount,
) -> list[OperatorComposition[FamilyNameT]]:
    compositions: list[OperatorComposition[FamilyNameT]] = []
    for chosen in combinations(selections, length):
        chosen_families = tuple(family for family, _unused in chosen)
        names = [family.name for family in chosen_families]
        if len(set(names)) != len(names):
            continue
        parameters = tuple(parameter for _unused, parameter in chosen)
        compositions.append(_ordered_composition(chosen_families, parameters))
    return compositions


def enumerate_candidates[FamilyNameT: OperatorFamilyName](
    families: tuple[OperatorFamily[FamilyNameT], ...],
    maximum_composed_atomic_actions: CompositionLengthLimit,
    source_sample_id: SampleIdentifier,
    cutoff_identity: SplitCutoffIdentity,
) -> tuple[OperatorCandidate[FamilyNameT], ...]:
    if maximum_composed_atomic_actions < 1:
        raise EnumerationContractError("maximum composed atomic actions must be at least one")
    ordered_families = tuple(sorted(families, key=lambda family: family.listed_order))
    listed_orders = [family.listed_order for family in ordered_families]
    if len(set(listed_orders)) != len(listed_orders):
        raise EnumerationContractError("operator families must have unique listed orders")
    selections: list[tuple[OperatorFamily[FamilyNameT], NormalizedParameterString]] = []
    for family in ordered_families:
        for parameter in sorted(family.parameter_grid):
            selections.append((family, parameter))

    candidates: list[OperatorCandidate[FamilyNameT]] = []
    seen: set[NormalizedOperatorFormText] = set()
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
    MALICIOUSNESS_VALIDATION_UNAVAILABLE = "MALICIOUSNESS_VALIDATION_UNAVAILABLE"


class ValidityLayerError(ValueError):
    pass


@dataclass(frozen=True)
class StructuralValidity:
    parser_primary_ok: ValidationFlag
    parser_secondary_ok: ValidationFlag
    expected_format_identity: ValidationFlag

    @property
    def is_valid(self) -> DomainValidityFlag:
        return self.parser_primary_ok and self.parser_secondary_ok and self.expected_format_identity


@dataclass(frozen=True)
class ExecutionSmokeValidity:
    source_launched: ValidationFlag
    transformed_launched: ValidationFlag
    no_new_crash_or_anr: ValidationFlag
    sandbox_identity_recorded: ValidationFlag
    within_timeout_seconds: TimeoutSeconds
    configured_timeout_seconds: TimeoutSeconds

    @property
    def is_valid(self) -> DomainValidityFlag:
        return (
            self.source_launched
            and self.transformed_launched
            and self.no_new_crash_or_anr
            and self.sandbox_identity_recorded
            and self.within_timeout_seconds <= self.configured_timeout_seconds
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
        if not self.maliciousness.source_detected:
            return ValidityStatus.MALICIOUSNESS_VALIDATION_UNAVAILABLE
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


def lamda_families() -> tuple[ApkOperatorFamily, ...]:
    return (
        OperatorFamily(
            name=ApkOperatorFamilyName.UNREACHABLE_BENIGN_GADGET_INJECTION,
            domain=OperatorDomain.ANDROID_APK,
            listed_order=0,
            parameter_grid=(NormalizedParameterString(f"gadget-library={BENIGN_GADGET_LIBRARY}"),),
        ),
        OperatorFamily(
            name=ApkOperatorFamilyName.PERMISSION_NEUTRAL_RESOURCE_INJECTION,
            domain=OperatorDomain.ANDROID_APK,
            listed_order=1,
            parameter_grid=tuple(
                NormalizedParameterString(f"payload={size}") for size in sorted(APK_PAYLOAD_SIZES)
            ),
        ),
    )


def pe_operator_enumerations() -> tuple[
    type[PeImportName], type[PeSectionRenameTarget], type[UpxAction]
]:
    return (PeImportName, PeSectionRenameTarget, UpxAction)


def pe_mutation_families() -> tuple[PeOperatorFamily, ...]:
    return (
        OperatorFamily(
            name=PeOperatorFamilyName.APPEND_BENIGN_EOF_BYTES,
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=0,
            parameter_grid=tuple(
                NormalizedParameterString(f"payload={size}") for size in sorted(PE_PAYLOAD_SIZES)
            ),
        ),
        OperatorFamily(
            name=PeOperatorFamilyName.FILL_EXISTING_SECTION_SLACK,
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=1,
            parameter_grid=tuple(
                NormalizedParameterString(f"payload={size} (truncated to available slack)")
                for size in sorted(PE_PAYLOAD_SIZES)
            ),
        ),
        OperatorFamily(
            name=PeOperatorFamilyName.ADD_UNUSED_IMPORT,
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=2,
            parameter_grid=tuple(
                NormalizedParameterString(f"import={name}") for name in sorted(PeImportName)
            ),
        ),
        OperatorFamily(
            name=PeOperatorFamilyName.RENAME_SECTION,
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=3,
            parameter_grid=tuple(
                NormalizedParameterString(f"section={item}")
                for item in sorted(PeSectionRenameTarget)
            ),
        ),
        OperatorFamily(
            name=PeOperatorFamilyName.ADD_READ_ONLY_SECTION,
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=4,
            parameter_grid=tuple(
                NormalizedParameterString(f"payload={size}")
                for size in sorted(PE_PAYLOAD_SIZES)
                if size != PayloadBytes(64)
            ),
        ),
        OperatorFamily(
            name=PeOperatorFamilyName.ENTRY_POINT_TRAMPOLINE,
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=5,
            parameter_grid=(NormalizedParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name=PeOperatorFamilyName.REMOVE_AUTHENTICODE_DIRECTORY,
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=6,
            parameter_grid=(NormalizedParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name=PeOperatorFamilyName.ZERO_PE_CHECKSUM,
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=7,
            parameter_grid=(NormalizedParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name=PeOperatorFamilyName.REMOVE_DEBUG_DIRECTORY,
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=8,
            parameter_grid=(NormalizedParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name=PeOperatorFamilyName.UPX_PACK_UNPACK,
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


class MutationStructuralIntegrityError(ValueError):
    pass


class PeFileHeader(Protocol):
    Machine: PeMachineCode


def _parameter_value(parameter: NormalizedParameterString) -> NormalizedParameterString:
    if "=" not in parameter:
        return parameter
    return NormalizedParameterString(parameter.split("=", 1)[1].split(" ", 1)[0])


def apply_pe_operator_family(
    family: PeOperatorFamily, parameter: NormalizedParameterString, pe_bytes: PeFileBytes
) -> PeFileBytes:
    value = _parameter_value(parameter)
    match family.name:
        case PeOperatorFamilyName.APPEND_BENIGN_EOF_BYTES:
            return append_benign_eof_bytes(pe_bytes, PayloadBytes(int(value)))
        case PeOperatorFamilyName.FILL_EXISTING_SECTION_SLACK:
            return fill_existing_section_slack(pe_bytes, PayloadBytes(int(value)))
        case PeOperatorFamilyName.ADD_UNUSED_IMPORT:
            return add_unused_import(pe_bytes, PeImportName(value))
        case PeOperatorFamilyName.RENAME_SECTION:
            return rename_section(pe_bytes, PeSectionRenameTarget(value))
        case PeOperatorFamilyName.ADD_READ_ONLY_SECTION:
            return add_read_only_section(pe_bytes, PayloadBytes(int(value)))
        case PeOperatorFamilyName.ENTRY_POINT_TRAMPOLINE:
            return add_entry_point_trampoline(pe_bytes)
        case PeOperatorFamilyName.REMOVE_AUTHENTICODE_DIRECTORY:
            return remove_authenticode_directory(pe_bytes)
        case PeOperatorFamilyName.ZERO_PE_CHECKSUM:
            return zero_pe_checksum(pe_bytes)
        case PeOperatorFamilyName.REMOVE_DEBUG_DIRECTORY:
            return remove_debug_directory(pe_bytes)
        case PeOperatorFamilyName.UPX_PACK_UNPACK:
            return apply_upx_action(pe_bytes, UpxAction(value))


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
        expected_format_identity=expected_machine_type,
    )


def structural_validity_status(pe_bytes: PeFileBytes) -> ValidityStatus:
    if structural_validity_of(pe_bytes).is_valid:
        return ValidityStatus.VALID
    return ValidityStatus.INVALID


def apply_and_verify_pe_operator_family(
    family: PeOperatorFamily, parameter: NormalizedParameterString, pe_bytes: PeFileBytes
) -> PeFileBytes:
    mutated = apply_pe_operator_family(family, parameter, pe_bytes)
    if structural_validity_status(mutated) is ValidityStatus.INVALID:
        raise MutationStructuralIntegrityError(
            f"mutation family {family.name!r} produced a structurally invalid PE file"
        )
    return mutated


def apk_structural_validity_of(apk_bytes: ApkFileBytes) -> StructuralValidity:
    try:
        apk = APK(cast(str, bytes(apk_bytes)), raw=True)
        primary_package = apk.get_package()
        parser_primary_ok = bool(primary_package)
    except Exception:
        parser_primary_ok = False
        primary_package = None

    with tempfile.TemporaryDirectory(prefix="fedact-apk-structural-") as scratch_directory:
        source_path = Path(scratch_directory) / "source.apk"
        source_path.write_bytes(bytes(apk_bytes))
        try:
            result = subprocess.run(
                [ToolchainComponent.AAPT2, "dump", "badging", source_path],
                check=True,
                capture_output=True,
            )
            badging_text = result.stdout.decode("utf-8", errors="replace")
            package_match = re.search(r"package: name='([^']+)'", badging_text)
            parser_secondary_ok = package_match is not None
            secondary_package = package_match.group(1) if package_match else None
        except subprocess.CalledProcessError:
            parser_secondary_ok = False
            secondary_package = None

    expected_format_identity = (
        parser_primary_ok
        and parser_secondary_ok
        and primary_package is not None
        and primary_package == secondary_package
    )
    return StructuralValidity(
        parser_primary_ok=parser_primary_ok,
        parser_secondary_ok=parser_secondary_ok,
        expected_format_identity=expected_format_identity,
    )


def apk_structural_validity_status(apk_bytes: ApkFileBytes) -> ValidityStatus:
    if apk_structural_validity_of(apk_bytes).is_valid:
        return ValidityStatus.VALID
    return ValidityStatus.INVALID


def apply_and_verify_apk_operator_family(
    family_name: ApkOperatorFamilyName,
    parameter: NormalizedParameterString,
    apk_bytes: ApkFileBytes,
    signing_identity: ApkSigningIdentity,
) -> ApkFileBytes:
    mutated = apply_apk_operator_family(family_name, parameter, apk_bytes, signing_identity)
    if apk_structural_validity_status(mutated) is ValidityStatus.INVALID:
        raise MutationStructuralIntegrityError(
            f"mutation family {family_name!r} produced a structurally invalid APK file"
        )
    return mutated


_CLAMSCAN_INFECTED_EXIT_CODE = 1
_CLAMAV_SYSTEM_SIGNATURE_DIRECTORY = Path("/var/lib/clamav")


def _clamscan_detected(
    file_path: Path, supplementary_signature_directory: Path | None
) -> ValidationFlag:
    command: list[str | Path] = [ToolchainComponent.CLAMSCAN, "--no-summary"]
    if supplementary_signature_directory is not None:
        command.extend(
            ["-d", _CLAMAV_SYSTEM_SIGNATURE_DIRECTORY, "-d", supplementary_signature_directory]
        )
    command.append(file_path)
    result = subprocess.run(command, capture_output=True, check=False)
    if result.returncode not in (0, _CLAMSCAN_INFECTED_EXIT_CODE):
        raise RuntimeError(
            f"clamscan failed on {file_path}: {result.stderr.decode(errors='replace')}"
        )
    return result.returncode == _CLAMSCAN_INFECTED_EXIT_CODE


def maliciousness_validity_of(
    source_bytes: RawPayloadBytes,
    transformed_bytes: RawPayloadBytes,
    file_suffix: FileSuffix,
    supplementary_signature_directory: Path | None = None,
) -> MaliciousnessValidity:
    with tempfile.TemporaryDirectory(prefix="fedact-maliciousness-") as scratch_directory:
        source_path = Path(scratch_directory) / f"source{file_suffix}"
        transformed_path = Path(scratch_directory) / f"transformed{file_suffix}"
        source_path.write_bytes(source_bytes)
        transformed_path.write_bytes(transformed_bytes)
        source_detected = _clamscan_detected(source_path, supplementary_signature_directory)
        transformed_detected = _clamscan_detected(
            transformed_path, supplementary_signature_directory
        )
    return MaliciousnessValidity(
        source_detected=source_detected,
        transformed_detected=transformed_detected,
    )


def apk_dynamic_validity_of(
    emulator: EmulatorHandle,
    source_apk_path: Path,
    transformed_apk_path: Path,
    package_name: AndroidPackageName,
    monkey_event_count: MonkeyEventCount,
    monkey_seed: SeedValue,
    execution_timeout_seconds: TimeoutSeconds,
    minimum_behavior_jaccard: SimilarityScore,
) -> tuple[ExecutionSmokeValidity, BehaviorValidity]:
    started = time.monotonic()
    source_result = run_dynamic_smoke(
        emulator, source_apk_path, package_name, monkey_event_count, monkey_seed
    )
    transformed_result = run_dynamic_smoke(
        emulator, transformed_apk_path, package_name, monkey_event_count, monkey_seed
    )
    elapsed = time.monotonic() - started
    smoke = ExecutionSmokeValidity(
        source_launched=source_result.launched,
        transformed_launched=transformed_result.launched,
        no_new_crash_or_anr=not (source_result.crashed_or_anr or transformed_result.crashed_or_anr),
        sandbox_identity_recorded=bool(emulator.serial),
        within_timeout_seconds=elapsed,
        configured_timeout_seconds=execution_timeout_seconds,
    )
    both_empty = not source_result.observable_events and not transformed_result.observable_events
    behavior = BehaviorValidity(
        jaccard_similarity=jaccard_similarity(
            source_result.observable_events, transformed_result.observable_events
        ),
        minimum_behavior_jaccard=minimum_behavior_jaccard,
        both_event_sets_empty=both_empty,
    )
    return smoke, behavior
