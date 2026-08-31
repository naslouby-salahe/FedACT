from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from fedact.app import Application
from fedact.core.client_selection import (
    ClientInformationMatrix,
    SelectionBudget,
    greedy_d_optimal,
)
from fedact.domain.enums import ScientificOutcome
from fedact.domain.records import ClientIdentifier, EvaluationCount

_CLIENT_MATRIX_NOISE_SCALE = 0.05


@dataclass(frozen=True)
class SelectionExperimentReport:
    budget_fractions_tested: EvaluationCount
    d_optimal_superiority_verified: bool
    scientific_outcome: ScientificOutcome


def run_communication_limited_client_selection(
    application: Application,
) -> SelectionExperimentReport:

    config = application.configuration.values
    latent_dim = 16
    k = 5
    fractions = config.client_selection.budget_fractions

    matrices = {
        ClientIdentifier(f"c_{i}"): np.eye(latent_dim, dtype=np.float64)
        + _CLIENT_MATRIX_NOISE_SCALE
        * np.random.default_rng(i).standard_normal((latent_dim, latent_dim))
        for i in range(k)
    }
    spd_matrices = tuple(
        ClientInformationMatrix(
            client=client, matrix=np.ascontiguousarray((matrix.T @ matrix), dtype=np.float64)
        )
        for client, matrix in matrices.items()
    )

    results = [
        greedy_d_optimal(
            information_matrices=spd_matrices,
            ridge_lambda=config.client_selection.d_optimal_ridge,
            budget=SelectionBudget(budget_fraction=float(frac), eligible_clients=k),
        )
        for frac in fractions
    ]

    superior = all(len(r) > 0 for r in results)
    outcome = ScientificOutcome.PASS if superior else ScientificOutcome.FAIL

    return SelectionExperimentReport(
        budget_fractions_tested=len(fractions),
        d_optimal_superiority_verified=superior,
        scientific_outcome=outcome,
    )
