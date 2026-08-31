from __future__ import annotations

from pathlib import Path

from fedact.domain.enums import ExecutableWorkflowName, ScientificOutcome
from fedact.storage.results import (
    WorkflowResultRecord,
    read_workflow_result,
    write_workflow_result,
)


def test_workflow_result_round_trip(tmp_path: Path) -> None:
    directory = tmp_path / "results" / "experiments" / "math-verification"
    record = WorkflowResultRecord(
        workflow=ExecutableWorkflowName.MATH_VERIFICATION,
        scientific_outcome=ScientificOutcome.PASS,
    )
    written = write_workflow_result(directory, record)
    assert written.is_file()
    loaded = read_workflow_result(directory)
    assert loaded is not None
    assert loaded.workflow is ExecutableWorkflowName.MATH_VERIFICATION
    assert loaded.scientific_outcome is ScientificOutcome.PASS


def test_workflow_result_with_metrics_round_trip(tmp_path: Path) -> None:
    directory = tmp_path / "results" / "experiments" / "prospective-evaluation"
    record = WorkflowResultRecord(
        workflow=ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
        scientific_outcome=ScientificOutcome.PASS,
        mean_false_negative_rate=0.08,
        mean_certification_rate=0.82,
        clean_fnr_degradation_percentage_points=0.9,
    )
    write_workflow_result(directory, record)
    loaded = read_workflow_result(directory)
    assert loaded is not None
    assert loaded.mean_false_negative_rate == 0.08
    assert loaded.mean_certification_rate == 0.82
    assert loaded.clean_fnr_degradation_percentage_points == 0.9


def test_missing_result_returns_none(tmp_path: Path) -> None:
    assert read_workflow_result(tmp_path / "missing") is None
