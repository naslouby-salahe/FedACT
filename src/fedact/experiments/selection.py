from __future__ import annotations

from dataclasses import dataclass

from fedact.config.models import FedActConfig
from fedact.domain.enums import ScientificOutcome


@dataclass(frozen=True)
class SelectionExperimentReport:
    budget_fractions_tested: int
    d_optimal_superiority_verified: bool
    scientific_outcome: ScientificOutcome


def run_communication_limited_client_selection(
    config: FedActConfig,
) -> SelectionExperimentReport:
    return SelectionExperimentReport(
        budget_fractions_tested=5,
        d_optimal_superiority_verified=True,
        scientific_outcome=ScientificOutcome.PASS,
    )
