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


class ScientificAssumption(StrEnum):
    CHRONOLOGY = "chronology"
    SHARED_COMPONENT = "shared-component"
    INFORMATIVE_CONTROLS = "informative-controls"
    CONTROL_SPAN_VALIDITY = "control-span-validity"
    PRIVATE_TRANSITION_ALLOWANCE = "private-transition-allowance"
    CUTOFF_FIXED_REPRESENTATION = "cutoff-fixed-representation"
    ACTION_VALIDITY = "action-validity"
    HISTORICAL_PREDICTABILITY = "historical-predictability"
    EIGENDECOMPOSITION_STABILITY = "eigendecomposition-stability"
    MINIMUM_SUPPORT = "minimum-support"
    PLAUSIBILITY_SET_COVERAGE = "plausibility-set-coverage"
    HONEST_PRIMARY_FEDERATION = "honest-primary-federation"
    OPERATOR_COVERAGE = "operator-coverage"
    TEMPORAL_STABILITY = "temporal-stability"


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


class RequiredScientificArtifact(StrEnum):
    RAW_DATA_AND_DATASET_PREPARATION_MANIFESTS = "raw-data-and-dataset-preparation-manifests"
    CHRONOLOGICAL_CUTOFF_AND_SPLIT_MANIFESTS = "chronological-cutoff-and-split-manifests"
    CLIENT_AND_COHORT_MANIFESTS = "client-and-cohort-manifests"
    FITTED_PREPROCESSING_TRANSFORMS = "fitted-preprocessing-transforms"
    CUTOFF_FIXED_REPRESENTATION_AND_DETECTOR_CHECKPOINTS = (
        "cutoff-fixed-representation-and-detector-checkpoints"
    )
    ENCODED_SCORED_OBSERVATIONS_AND_TRANSITION_SUMMARIES = (
        "encoded-scored-observations-and-transition-summaries"
    )
    CLIENT_NUISANCE_BASES_AND_CONSTRAINTS = "client-nuisance-bases-and-constraints"
    HISTORICAL_REFERENCE_POINTS_RADII_FEASIBLE_SETS_AND_CENTERS = (
        "historical-reference-points-radii-feasible-sets-and-centers"
    )
    TEMPORAL_MODEL_AND_PROCESS_ERROR_SETS = "temporal-model-and-process-error-sets"
    NESTED_CALIBRATION_RESULTS = "nested-calibration-results"
    OPERATOR_LIBRARY_IDENTITIES_VALIDITY_RECORDS_AND_ACTION_DISPLACEMENTS = (
        "operator-library-identities-validity-records-and-action-displacements"
    )
    PROSPECTIVE_FEASIBLE_SETS_AND_DIAMETER_BOUNDS = "prospective-feasible-sets-and-diameter-bounds"
    ACTION_INTERVALS_STATES_CERTIFICATES_AND_ABSTENTIONS = (
        "action-intervals-states-certificates-and-abstentions"
    )
    HARDENED_AND_BASELINE_CHECKPOINTS = "hardened-and-baseline-checkpoints"
    WORKFLOW_RESULTS_AND_STATISTICAL_SUMMARIES = "workflow-results-and-statistical-summaries"
    MANUSCRIPT_FACING_EVIDENCE = "manuscript-facing-evidence"


class ExecutableWorkflowName(StrEnum):
    PREPROCESS = "preprocess"
    SMOKE = "smoke"
    BASELINE_PARITY = "baseline-parity"
    NESTED_CALIBRATION = "nested-calibration"
    MATH_VERIFICATION = "math-verification"
    SYNTHETIC_GEOMETRY = "synthetic-geometry"
    ACTION_CERTIFICATE_VALIDATION = "action-certificate-validation"
    PROSPECTIVE_EVALUATION = "prospective-evaluation"
    ABLATIONS = "ablations"
    FEDERATION = "federation"
    FAILURE_BOUNDARIES = "failure-boundaries"
    CROSS_CORPUS = "cross-corpus"
    CLIENT_SELECTION = "client-selection"
    STATISTICAL_SYNTHESIS = "statistical-synthesis"


class DatasetSelector(StrEnum):
    LAMDA = "lamda"
    EMBER2024 = "ember2024"
