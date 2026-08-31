from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner, Result

from fedact.app import Application, discover_repository_root
from fedact.artifacts.manifests import WorkflowResultRecord, write_workflow_result
from fedact.cli.main import app
from fedact.domain.enums import ExecutableWorkflowName, ScientificOutcome

RUNNER = CliRunner()


def invoke(*arguments: str) -> Result:
    return RUNNER.invoke(app, list(arguments))


def test_plan_lists_all_workflows_in_dependency_order(repository_root: Path) -> None:
    result = invoke("plan", "--repository-root", str(repository_root))
    assert result.exit_code == 0
    names = [line.split(":")[0] for line in result.output.splitlines()]
    assert names[0] == "preprocess"
    assert "math-verification" in names
    assert names[-1] == "statistical-synthesis"
    assert any("[optional]" in line for line in result.output.splitlines())


def test_doctor_reports_configuration_hash_and_readiness(repository_root: Path) -> None:
    result = invoke("doctor", "--repository-root", str(repository_root))
    assert result.exit_code == 0
    assert "configuration_hash: sha256:" in result.output
    assert "raw_data_available:" in result.output


def test_status_without_argument_lists_all_workflows(repository_root: Path) -> None:
    result = invoke("status", "--repository-root", str(repository_root))
    assert result.exit_code == 0
    assert "math-verification: NOT_STARTED" in result.output


def test_status_for_named_workflow_reports_state(repository_root: Path) -> None:
    result = invoke("status", "synthetic-geometry", "--repository-root", str(repository_root))
    assert result.exit_code == 0
    assert "workflow: synthetic-geometry" in result.output
    assert "status: BLOCKED" in result.output


def test_unknown_workflow_is_rejected(repository_root: Path) -> None:
    result = invoke("run", "not-a-workflow", "--repository-root", str(repository_root))
    assert result.exit_code == 2


def test_blocked_workflow_cannot_run(repository_root: Path) -> None:
    result = invoke("run", "ablations", "--repository-root", str(repository_root))
    assert result.exit_code == 2
    assert "blocked by" in result.output


def test_executable_workflow_runs_when_producer_is_registered(
    repository_root: Path,
) -> None:
    result = invoke("run", "math-verification", "--repository-root", str(repository_root))
    assert result.exit_code == 0
    assert "mathematical verification completed: PASS" in result.output


def test_overwrite_flag_is_accepted_on_run(repository_root: Path) -> None:
    result = invoke(
        "run", "math-verification", "--overwrite", "--repository-root", str(repository_root)
    )
    assert result.exit_code == 0
    assert "overwrite: scoped to this workflow's artifacts" in result.output


def test_prohibited_scientific_flags_do_not_exist(repository_root: Path) -> None:
    for forbidden in [
        ["run", "math-verification", "--seed", "5"],
        ["run", "math-verification", "--threshold", "0.9"],
        ["smoke", "--dataset", "lamda"],
        ["plan", "--horizon", "6"],
    ]:
        result = invoke(*forbidden, "--repository-root", str(repository_root))
        assert result.exit_code != 0, f"prohibited flag accepted: {forbidden}"


def test_preprocess_requires_a_defined_selector(repository_root: Path) -> None:
    result = invoke("preprocess", "mnist", "--repository-root", str(repository_root))
    assert result.exit_code == 2


def test_preprocess_accepts_defined_selectors_and_scoped_overwrite(
    repository_root: Path,
) -> None:
    plain = invoke("preprocess", "--repository-root", str(repository_root))
    selected = invoke("preprocess", "lamda", "--repository-root", str(repository_root))
    scoped = invoke(
        "preprocess", "ember2024", "--overwrite", "--repository-root", str(repository_root)
    )
    for result, scope in ((plain, "lamda ember2024"), (selected, "lamda"), (scoped, "ember2024")):
        assert result.exit_code == 0
        assert scope in result.output


def test_smoke_supports_only_the_locked_form(repository_root: Path) -> None:
    result = invoke("smoke", "--repository-root", str(repository_root))
    assert result.exit_code == 0
    assert "smoke validation passed" in result.output
    scoped = invoke("smoke", "--overwrite", "--repository-root", str(repository_root))
    assert scoped.exit_code == 0
    assert "overwrite: scoped to smoke-owned artifacts" in scoped.output


def test_report_forms_validate_workflow_names(repository_root: Path) -> None:
    invalid = invoke("report", "bogus", "--repository-root", str(repository_root))
    assert invalid.exit_code == 2

    without_data = invoke("report", "--repository-root", str(repository_root))
    assert without_data.exit_code == 1
    assert "requires a completed prospective evaluation result" in without_data.output

    application = Application.from_repository_root(discover_repository_root(repository_root))
    write_workflow_result(
        application.result_experiment_directory(ExecutableWorkflowName.PROSPECTIVE_EVALUATION),
        WorkflowResultRecord(
            workflow=ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
            scientific_outcome=ScientificOutcome.PASS,
            mean_false_negative_rate=0.08,
            mean_certification_rate=0.82,
            clean_fnr_degradation_percentage_points=0.9,
        ),
    )
    valid = invoke(
        "report",
        "prospective-evaluation",
        "--overwrite",
        "--repository-root",
        str(repository_root),
    )
    assert valid.exit_code == 0
    assert "manuscript evidence reporting completed: PASS" in valid.output
    summary = (repository_root / "results" / "project_summary.json").read_text(encoding="utf-8")
    assert "0.08" in summary
    assert "0.82" in summary
