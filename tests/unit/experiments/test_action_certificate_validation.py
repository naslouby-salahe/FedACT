from __future__ import annotations

import json
from pathlib import Path

import pytest

from fedact.domain.types import ScientificOutcome
from fedact.experiments.validation import run_action_certificate_validation
from fedact.workflow import Application


def test_action_validation_requires_calibrated_executable_operators(
    application: Application,
) -> None:
    report = run_action_certificate_validation(application)
    assert report.total_actions == 0
    assert report.scientific_outcome is ScientificOutcome.INSUFFICIENT_EVIDENCE


@pytest.fixture
def isolated_application(tmp_path: Path, application: Application) -> Application:
    return Application(repository_root=tmp_path, configuration=application.configuration)


def _action(
    sample_id: str,
    lower_bound: float,
    upper_bound: float,
    point_score: float,
    later_real_alignment_score: float,
) -> dict[str, object]:
    return {
        "sample_id": sample_id,
        "lower_bound": lower_bound,
        "upper_bound": upper_bound,
        "domain_valid": True,
        "set_diameter": 0.5,
        "historical_diameter_quantile": 1.0,
        "cutoff_id": "c1",
        "cohort": "cohort-a",
        "horizon_step": 1,
        "source_sample_id": "shared-source",
        "action_count": 1,
        "point_score": point_score,
        "later_real_alignment_score": later_real_alignment_score,
    }


def _write_fixture(application: Application) -> None:
    actions_dir = (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / "action-certificate-validation"
    )
    actions_dir.mkdir(parents=True, exist_ok=True)
    actions = [
        _action("cert-1", 0.6, 0.7, point_score=0.55, later_real_alignment_score=0.9),
        _action("cert-2", 0.6, 0.7, point_score=0.52, later_real_alignment_score=0.9),
        _action("high-point-1", 0.1, 0.9, point_score=0.95, later_real_alignment_score=0.6),
        _action("high-point-2", 0.1, 0.9, point_score=0.90, later_real_alignment_score=0.4),
    ]
    actions.extend(
        _action(f"filler-{i}", 0.1, 0.9, point_score=0.1, later_real_alignment_score=0.1)
        for i in range(20)
    )
    (actions_dir / "actions.json").write_text(json.dumps({"actions": actions}), encoding="utf-8")

    calibration_dir = (
        application.repository_root
        / application.configuration.values.workspace.directories.experiments
        / "nested-calibration"
    )
    calibration_dir.mkdir(parents=True, exist_ok=True)
    (calibration_dir / "selected.json").write_text(
        json.dumps(
            {
                "candidate_id": "primary",
                "tau_align": 0.5,
                "tau_amb": 0.3,
                "hardening_weight": 1.0,
            }
        ),
        encoding="utf-8",
    )


def test_action_validation_detects_certified_over_point_over_random_pattern(
    isolated_application: Application,
) -> None:
    _write_fixture(isolated_application)
    report = run_action_certificate_validation(isolated_application)
    assert report.total_actions == 24
    assert report.certified_positive_count == 2
    assert report.central_pattern_supported is True
    assert report.scientific_outcome is ScientificOutcome.PASS
    assert report.rank_alignment_spearman_rho is not None
