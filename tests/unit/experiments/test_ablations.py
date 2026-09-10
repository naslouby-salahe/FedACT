from __future__ import annotations

import json
from pathlib import Path

import pytest

from fedact.domain.types import ScientificOutcome
from fedact.experiments.robustness import run_novelty_critical_ablations
from fedact.workflow import Application


def test_ablation_requires_completed_prospective_evidence(application: Application) -> None:
    report = run_novelty_critical_ablations(application)
    assert report.evaluated_configurations == 0
    assert report.scientific_outcome is ScientificOutcome.INSUFFICIENT_EVIDENCE


@pytest.fixture
def isolated_application(tmp_path: Path, application: Application) -> Application:
    return Application(repository_root=tmp_path, configuration=application.configuration)


def test_hardening_off_ablation_measures_real_degradation(
    isolated_application: Application,
) -> None:
    destination = (
        isolated_application.repository_root
        / isolated_application.configuration.values.workspace.directories.experiments
        / "prospective-evaluation"
        / "cutoff-comparisons.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "comparisons": [
                    {
                        "cutoff_id": "lamda-1",
                        "hardened_false_negative_rate": 0.1,
                        "static_chronological_false_negative_rate": 0.4,
                    },
                    {
                        "cutoff_id": "lamda-2",
                        "hardened_false_negative_rate": 0.2,
                        "static_chronological_false_negative_rate": 0.5,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    report = run_novelty_critical_ablations(isolated_application)
    assert report.evaluated_configurations == 1
    assert report.scientific_outcome is ScientificOutcome.PASS
    result = report.results[0]
    assert result.ablation_name == "hardening_off"
    assert result.degradation_percentage_points == pytest.approx(30.0)
