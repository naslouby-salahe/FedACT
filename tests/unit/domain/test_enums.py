from __future__ import annotations

from fedact.domain.types import ArtifactBoundary, ScientificOutcome


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
