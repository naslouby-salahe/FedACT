from __future__ import annotations

from enum import StrEnum


class WorkflowName(StrEnum):
    SCIENTIFIC_AND_CONFIGURATION_AUTHORITY = "scientific-and-configuration-authority"
    MATHEMATICAL_AND_NUMERICAL_VERIFICATION = "mathematical-and-numerical-verification"
    SYNTHETIC_GENERATOR_SMOKE_VALIDATION = "synthetic-generator-smoke-validation"
    SYNTHETIC_THEORY_AND_GEOMETRY_VALIDATION = "synthetic-theory-and-geometry-validation"
    REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT = "real-data-feasibility-and-control-audit"
    BASELINE_REPRODUCTION_AND_PARITY_VALIDATION = "baseline-reproduction-and-parity-validation"
    NESTED_PRE_CUTOFF_CALIBRATION = "nested-pre-cutoff-calibration"
    REAL_DATA_ACTION_CERTIFICATE_VALIDATION = "real-data-action-certificate-validation"
    MAIN_PROSPECTIVE_FEDACT_EVALUATION = "main-prospective-fedact-evaluation"
    NOVELTY_CRITICAL_ABLATIONS = "novelty-critical-ablations"
    FEDERATION_AND_COMPLEMENTARITY_EVALUATION = "federation-and-complementarity-evaluation"
    ROBUSTNESS_AND_FAILURE_BOUNDARY_EVALUATION = "robustness-and-failure-boundary-evaluation"
    CROSS_CORPUS_GENERALIZATION = "cross-corpus-generalization"
    COMMUNICATION_LIMITED_CLIENT_SELECTION = "communication-limited-client-selection"
    STATISTICAL_SYNTHESIS = "statistical-synthesis"
    MANUSCRIPT_EVIDENCE_GENERATION = "manuscript-evidence-generation"


class ScientificOutcome(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    INFEASIBLE = "INFEASIBLE"
    NUMERICAL_FAILURE = "NUMERICAL_FAILURE"
    ASSUMPTION_VIOLATION = "ASSUMPTION_VIOLATION"
    ABSTENTION_EXPECTED = "ABSTENTION_EXPECTED"


class ArtifactLifecycleState(StrEnum):
    PLANNED = "planned"
    STAGING = "staging"
    COMPLETE = "complete"
    REUSED = "reused"
    STALE = "stale"
    REPLACED = "replaced"
    INCOMPLETE = "incomplete"
    CLEANED = "cleaned"


class ArtifactBoundary(StrEnum):
    INPUTS = "inputs"
    DATASET_PREPARATION = "dataset-preparation"
    PREPROCESSING_AND_SPLITS = "preprocessing-and-splits"
    TRAINING_CHECKPOINTS = "training-checkpoints"
    SCORING_AND_SUMMARIES = "scoring-and-summaries"
    CALIBRATION_AND_CERTIFICATION = "calibration-and-certification"
    EVALUATION = "evaluation"
    ANALYSIS = "analysis"
    REPORTING = "reporting"
