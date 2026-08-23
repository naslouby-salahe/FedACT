from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

from fedact.domain.assumptions import AssumptionConsequence
from fedact.domain.enums import ScientificAssumption, ScientificOutcome
from fedact.domain.operators.contracts import OperatorDomain
from fedact.domain.records import SplitCutoffIdentity

CoverageRatio = NewType("CoverageRatio", float)


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
    operator_name: str
    domain: OperatorDomain
    cutoff_identity: SplitCutoffIdentity
    structural_valid: bool
    execution_valid: bool
    maliciousness_preserved: bool
    behavior_preserved: bool

    def is_domain_valid(self) -> bool:
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
    operator_eligible_source_samples: int
    samples_with_valid_nondegenerate_candidate: int
    minimum_valid_coverage: float

    @property
    def observed_coverage(self) -> CoverageRatio | None:
        denominator = self.operator_eligible_source_samples
        if denominator == 0:
            return None
        return CoverageRatio(self.samples_with_valid_nondegenerate_candidate / denominator)

    def is_coverage_sufficient(self) -> bool:
        coverage = self.observed_coverage
        if coverage is None:
            raise OperatorCoverageError(
                "operator-dependent execution must emit ABSTAIN_OPERATOR_COVERAGE_INSUFFICIENT "
                "when the operator-eligible denominator is zero"
            )
        return coverage >= self.minimum_valid_coverage
