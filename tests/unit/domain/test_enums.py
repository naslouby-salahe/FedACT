from __future__ import annotations

from fedact.domain.enums import (
    ArtifactBoundary,
    ArtifactLifecycleState,
    ScientificOutcome,
    WorkflowName,
)


def test_workflow_names_match_roadmap_titles_exactly() -> None:
    assert {workflow.value for workflow in WorkflowName} == {
        "scientific-and-configuration-authority",
        "mathematical-and-numerical-verification",
        "synthetic-generator-smoke-validation",
        "synthetic-theory-and-geometry-validation",
        "real-data-feasibility-and-control-audit",
        "baseline-reproduction-and-parity-validation",
        "nested-pre-cutoff-calibration",
        "real-data-action-certificate-validation",
        "main-prospective-fedact-evaluation",
        "novelty-critical-ablations",
        "federation-and-complementarity-evaluation",
        "robustness-and-failure-boundary-evaluation",
        "cross-corpus-generalization",
        "communication-limited-client-selection",
        "statistical-synthesis",
        "manuscript-evidence-generation",
    }


def test_scientific_outcomes_are_the_exact_roadmap_vocabulary() -> None:
    assert {outcome.value for outcome in ScientificOutcome} == {
        "PASS",
        "FAIL",
        "INSUFFICIENT_EVIDENCE",
        "INFEASIBLE",
        "NUMERICAL_FAILURE",
        "ASSUMPTION_VIOLATION",
        "ABSTENTION_EXPECTED",
    }


def test_lifecycle_states_cover_the_locked_state_space() -> None:
    assert {state.value for state in ArtifactLifecycleState} == {
        "planned",
        "staging",
        "complete",
        "reused",
        "stale",
        "replaced",
        "incomplete",
        "cleaned",
    }


def test_artifact_boundaries_are_the_nine_roadmap_boundaries() -> None:
    assert {boundary.value for boundary in ArtifactBoundary} == {
        "inputs",
        "dataset-preparation",
        "preprocessing-and-splits",
        "training-checkpoints",
        "scoring-and-summaries",
        "calibration-and-certification",
        "evaluation",
        "analysis",
        "reporting",
    }
