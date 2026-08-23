from __future__ import annotations

from fedact.domain.enums import ScientificAssumption, ScientificOutcome
from fedact.fedact.contracts import FEDACT_ASSUMPTION_CONTRACTS


def test_abstention_vs_fail_semantics_in_contracts() -> None:
    control_contract = FEDACT_ASSUMPTION_CONTRACTS[ScientificAssumption.INFORMATIVE_CONTROLS]
    assert control_contract.failure_outcome is ScientificOutcome.ASSUMPTION_VIOLATION

    honest_contract = FEDACT_ASSUMPTION_CONTRACTS[ScientificAssumption.HONEST_PRIMARY_FEDERATION]
    assert honest_contract.failure_outcome is ScientificOutcome.FAIL
