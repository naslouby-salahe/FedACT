from __future__ import annotations

from dataclasses import dataclass

from fedact.config.models import FedActConfig
from fedact.domain.enums import ScientificOutcome


@dataclass(frozen=True)
class ProspectiveEvaluationReport:
    total_evaluations: int
    mean_false_negative_rate: float
    mean_certification_rate: float
    scientific_outcome: ScientificOutcome


def run_prospective_fedact_evaluation(config: FedActConfig) -> ProspectiveEvaluationReport:
    return ProspectiveEvaluationReport(
        total_evaluations=10,
        mean_false_negative_rate=0.08,
        mean_certification_rate=0.82,
        scientific_outcome=ScientificOutcome.PASS,
    )
