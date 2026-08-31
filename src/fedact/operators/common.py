from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from itertools import combinations
from typing import NewType

from fedact.domain.enums import ScientificAssumption, ScientificOutcome
from fedact.domain.records import (
    AssumptionConsequence,
    DatasetName,
    DomainValidityFlag,
    FamilyName,
    MetricRate,
    NormalizedOperatorFormText,
    NormValue,
    OperatorIdentifier,
    OrderIndex,
    ProvenanceText,
    RuleDescription,
    SampleCount,
    SampleIdentifier,
    SplitCutoffIdentity,
    SufficiencyFlag,
    ThresholdValue,
    UsageCount,
    ValidationFlag,
)

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
) -> str:
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
    length: int,
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
    structural_valid: bool
    execution_valid: bool
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
