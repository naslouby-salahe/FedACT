from __future__ import annotations

from fedact.domain.operators.contracts import OperatorFamily
from fedact.operators.common import pe_mutation_families


def ember2024_families() -> tuple[OperatorFamily, ...]:
    return pe_mutation_families()
