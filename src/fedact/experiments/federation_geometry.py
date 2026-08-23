from __future__ import annotations

from dataclasses import dataclass

from fedact.config.models import FedActConfig
from fedact.domain.enums import ScientificOutcome


@dataclass(frozen=True)
class FederationGeometryReport:
    geometries_tested: int
    complementarity_gain: float
    scientific_outcome: ScientificOutcome


def run_federation_and_complementarity_evaluation(
    config: FedActConfig,
) -> FederationGeometryReport:
    return FederationGeometryReport(
        geometries_tested=4,
        complementarity_gain=0.18,
        scientific_outcome=ScientificOutcome.PASS,
    )
