from __future__ import annotations

import json
from pathlib import Path

import pytest

from fedact.domain.types import ScientificOutcome
from fedact.experiments.generalization import (
    read_central_pattern_cutoff_aggregates,
    run_prospective_fedact_evaluation,
)
from fedact.workflow import Application


def test_prospective_evaluation_never_fabricates_missing_lamda_evidence(
    application: Application,
) -> None:
    report = run_prospective_fedact_evaluation(application)
    assert report.total_evaluations == 0
    assert 0.0 <= report.mean_false_negative_rate <= 1.0
    assert 0.0 <= report.mean_certification_rate <= 1.0
    assert report.scientific_outcome is ScientificOutcome.INSUFFICIENT_EVIDENCE


@pytest.fixture
def isolated_application(tmp_path: Path, application: Application) -> Application:
    return Application(repository_root=tmp_path, configuration=application.configuration)


def test_read_central_pattern_cutoff_aggregates_excludes_insufficient_match_quality(
    isolated_application: Application,
) -> None:
    destination = (
        isolated_application.repository_root
        / isolated_application.configuration.values.workspace.directories.experiments
        / "action-certificate-validation"
        / "central-pattern.json"
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            {
                "cutoffs": [
                    {
                        "cutoff_id": "lamda-1",
                        "certified_precision": 0.9,
                        "point_selected_precision": 0.5,
                        "matched_random_precision": 0.2,
                        "matched_random_match_quality_sufficient": True,
                    },
                    {
                        "cutoff_id": "lamda-2",
                        "certified_precision": 0.8,
                        "point_selected_precision": 0.4,
                        "matched_random_precision": 0.3,
                        "matched_random_match_quality_sufficient": False,
                    },
                ],
                "rank_alignment_spearman_rho": 0.6,
            }
        ),
        encoding="utf-8",
    )
    certified, matched_random = read_central_pattern_cutoff_aggregates(isolated_application)
    assert len(certified) == 1
    assert len(matched_random) == 1
    assert certified[0].cutoff_identity == "lamda-1"
    assert certified[0].value == pytest.approx(0.9)
    assert matched_random[0].value == pytest.approx(0.2)
