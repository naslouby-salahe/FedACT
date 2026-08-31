from __future__ import annotations

from typer.testing import CliRunner

from fedact.cli.main import app
from fedact.domain.enums import ArtifactBoundary, DatasetSelector
from fedact.domain.records import DependencyFingerprint
from fedact.experiments.dependencies import (
    PREPROCESS_OWNED_BOUNDARIES,
    PREPROCESS_STAGE_FLOW,
    OverwriteRequest,
    ReuseDecision,
    SharedProducer,
    is_preprocess_triggerable,
    ownership_for,
    resolve_reuse_or_recompute,
)

runner = CliRunner()


def test_preprocess_without_selector_covers_both_real_datasets() -> None:
    result = runner.invoke(app, ["preprocess", "--repository-root", "."])
    assert result.exit_code == 0
    assert "preprocess scope: lamda ember2024" in result.output


def test_preprocess_with_selector_processes_only_that_corpus() -> None:
    result = runner.invoke(app, ["preprocess", "lamda", "--repository-root", "."])
    assert result.exit_code == 0
    assert "preprocess scope: lamda" in result.output
    assert "ember2024" not in result.output


def test_preprocess_derives_first_and_last_cutoff_from_the_release() -> None:
    result = runner.invoke(app, ["preprocess", "ember2024", "--repository-root", "."])
    assert result.exit_code == 0
    assert "first_cutoff=month-000012" in result.output
    assert "last_cutoff=month-000015" in result.output


def test_lamda_chronology_audit_fails_when_history_bridges_2015() -> None:
    result = runner.invoke(app, ["preprocess", "lamda", "--repository-root", "."])
    assert result.exit_code == 0
    assert "chronology_audit=" in result.output


def test_overwrite_scopes_to_preprocess_owned_artifacts_only() -> None:
    result = runner.invoke(app, ["preprocess", "lamda", "--overwrite", "--repository-root", "."])
    assert result.exit_code == 0
    assert "overwrite: scoped to preprocess-owned artifacts" in result.output


def test_preprocess_never_triggers_calibration_or_baseline_producers_directly() -> None:
    assert is_preprocess_triggerable(SharedProducer.REPRESENTATION_DETECTOR_FIT)
    assert not is_preprocess_triggerable(SharedProducer.NESTED_PRE_CUTOFF_CALIBRATION)
    assert not is_preprocess_triggerable(SharedProducer.BASELINE_FIT_PARITY)


def test_shared_producer_reuse_scopes_match_the_roadmap_table() -> None:
    fit = ownership_for(SharedProducer.REPRESENTATION_DETECTOR_FIT)
    scoring = ownership_for(SharedProducer.ENCODING_SCORING_AND_SUMMARIES)
    calibration = ownership_for(SharedProducer.NESTED_PRE_CUTOFF_CALIBRATION)
    assert "§9.5" in fit.reuse_scope
    assert "same checkpoint" in scoring.reuse_scope
    assert "dataset/cutoff" in calibration.reuse_scope


def test_preprocess_owned_boundaries_are_exactly_the_two_data_boundaries() -> None:
    assert set(PREPROCESS_OWNED_BOUNDARIES) == {
        ArtifactBoundary.DATASET_PREPARATION,
        ArtifactBoundary.PREPROCESSING_AND_SPLITS,
    }


def test_stage_flow_preserves_the_locked_ordering() -> None:
    names = [stage.name for stage in PREPROCESS_STAGE_FLOW]
    assert names[0] == "raw discovery/checksum"
    assert names[1] == "normalized parsed preparation"
    assert names[2] == "chronology/cutoff construction"
    assert names[-1] == "real-data audits"
    orders = [stage.stage_order for stage in PREPROCESS_STAGE_FLOW]
    assert orders == sorted(orders)


def test_reuse_decision_distinguishes_compatible_stale_and_overwrite() -> None:
    fingerprint = DependencyFingerprint("sha256:same")
    keep = OverwriteRequest(requested=False)
    force = OverwriteRequest(requested=True)
    assert resolve_reuse_or_recompute(fingerprint, fingerprint, keep) is ReuseDecision.REUSE
    other = DependencyFingerprint("sha256:other")
    assert resolve_reuse_or_recompute(other, fingerprint, keep) is ReuseDecision.STALE
    assert resolve_reuse_or_recompute(None, fingerprint, keep) is ReuseDecision.STALE
    assert resolve_reuse_or_recompute(fingerprint, fingerprint, force) is ReuseDecision.OVERWRITE


def test_dataset_selectors_are_the_exact_roadmap_corpus_names() -> None:
    assert {item.value for item in DatasetSelector} == {"lamda", "ember2024"}
