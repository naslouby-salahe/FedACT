from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import NewType

from fedact.domain.records import SampleIdentifier, SplitCutoffIdentity
from fedact.domain.types import (
    CanonicalFormText,
    DatasetName,
    FamilyName,
    NormValue,
    OrderIndex,
    ProvenanceText,
    RuleDescription,
    ThresholdValue,
    UsageCount,
)

OperatorName = NewType("OperatorName", str)
CanonicalParameterString = NewType("CanonicalParameterString", str)
OutputHash = NewType("OutputHash", str)


class OperatorDomain(StrEnum):
    WINDOWS_PE = "windows-pe"
    ANDROID_APK = "android-apk"


@dataclass(frozen=True)
class OperatorFamily:
    name: FamilyName
    domain: OperatorDomain
    listed_order: OrderIndex
    parameter_grid: tuple[CanonicalParameterString, ...]


@dataclass(frozen=True)
class OperatorRecord:
    operator_name: OperatorName
    dataset: DatasetName
    domain: OperatorDomain
    semantic_validity_contract: RuleDescription
    construction_function: RuleDescription
    parameter_domain: tuple[CanonicalParameterString, ...]
    eligibility_rule: RuleDescription
    rejection_rule: RuleDescription
    representation_displacement_rule: RuleDescription
    zero_displacement_rule: RuleDescription
    maximum_uses_per_sample: UsageCount
    provenance: ProvenanceText


@dataclass(frozen=True)
class OperatorComposition:
    families: tuple[OperatorFamily, ...]
    parameters: tuple[CanonicalParameterString, ...]

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
    canonical_form: CanonicalFormText
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
