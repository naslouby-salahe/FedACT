from __future__ import annotations

import json
from pathlib import Path

import pytest

from fedact.domain.types import ScientificOutcome
from fedact.experiments.robustness import run_communication_limited_client_selection
from fedact.workflow import Application


def test_client_selection_requires_materialized_client_information(
    application: Application,
) -> None:
    report = run_communication_limited_client_selection(application)
    assert report.budget_fractions_tested == 0
    assert report.scientific_outcome is ScientificOutcome.INSUFFICIENT_EVIDENCE


@pytest.fixture
def isolated_application(tmp_path: Path, application: Application) -> Application:
    return Application(repository_root=tmp_path, configuration=application.configuration)


def _write_clients_fixture(application: Application) -> None:
    destination = (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / "federation"
        / "clients.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    clients = []
    malicious_counts = {"client-a": (8, 12), "client-b": (2, 3), "client-c": (5, 5)}
    well_conditioned_features = {
        "client-a": [[3.0, 1.0], [1.0, 3.0], [2.5, 1.5], [1.5, 2.5], [2.0, 2.0], [3.5, 0.5]],
        "client-b": [[6.0, 2.0], [2.0, 6.0], [5.0, 3.0], [3.0, 5.0], [4.0, 4.0], [7.0, 1.0]],
        "client-c": [[9.0, 3.0], [3.0, 9.0], [7.5, 4.5], [4.5, 7.5], [6.0, 6.0], [10.5, 1.5]],
    }
    for client_id in ("client-a", "client-b", "client-c"):
        sample_count = 6
        clients.append(
            {
                "client_id": client_id,
                "sample_ids": [f"{client_id}-{i}" for i in range(sample_count)],
                "features": well_conditioned_features[client_id],
                "month_indices": [i for i in range(sample_count)],
                "labels": [bool(i % 2) for i in range(sample_count)],
                "historical_malicious_count": malicious_counts[client_id][0],
                "later_malicious_count": malicious_counts[client_id][1],
            }
        )
    payload = {
        "clients": clients,
        "candidate_action_directions": [[1.0, 0.0], [0.0, 1.0]],
        "historical_plausibility_radius": 1.0,
    }
    destination.write_text(json.dumps(payload), encoding="utf-8")


def test_client_selection_runs_all_four_comparators_on_real_client_data(
    isolated_application: Application,
) -> None:
    _write_clients_fixture(isolated_application)
    report = run_communication_limited_client_selection(isolated_application)
    assert report.scientific_outcome is ScientificOutcome.PASS
    assert report.budget_fractions_tested == 3
    comparators = {item.comparator for item in report.comparator_reductions}
    assert comparators == {
        "random",
        "largest_sample_count",
        "global_information",
        "action_interval_contraction",
    }
    for item in report.comparator_reductions:
        assert item.total_reduction >= 0.0
