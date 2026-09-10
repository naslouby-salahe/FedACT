from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Annotated, NewType

from pydantic import Field, JsonValue, StringConstraints


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


class MissingCutoffReason(StrEnum):
    INFRASTRUCTURE_FAILURE = "INFRASTRUCTURE_FAILURE"
    NUMERICAL_FAILURE = "NUMERICAL_FAILURE"
    SCIENTIFIC_INFEASIBILITY = "SCIENTIFIC_INFEASIBILITY"
    ASSUMPTION_VIOLATION = "ASSUMPTION_VIOLATION"
    EXPECTED_ABSTENTION = "EXPECTED_ABSTENTION"
    MISSING_SOURCE_DATA = "MISSING_SOURCE_DATA"


class EffectDirection(StrEnum):
    FAVORABLE = "FAVORABLE"
    CONTRADICTORY = "CONTRADICTORY"
    NEUTRAL = "NEUTRAL"


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


class RunnableWorkflowName(StrEnum):
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


class FederationGeometry(StrEnum):
    REDUNDANT = "redundant"
    COMPLEMENTARY = "complementary"


class RankSelectionMethod(StrEnum):
    FIXED_RANK = "FIXED_RANK"
    EIGENGAP = "EIGENGAP"
    VARIANCE_THRESHOLD = "VARIANCE_THRESHOLD"


class CertificationStatus(StrEnum):
    CERTIFIED_POSITIVE = "CERTIFIED_POSITIVE"
    CERTIFIED_NEGATIVE = "CERTIFIED_NEGATIVE"
    AMBIGUOUS = "AMBIGUOUS"
    ABSTAIN = "ABSTAIN"


class ArtifactVerificationStatus(StrEnum):
    VERIFIED = "verified"
    MISSING = "missing"


class ConfirmatoryFormat(StrEnum):
    WIN32_PE = "win32_pe"
    WIN64_PE = "win64_pe"


class PrivateTransitionSparsityMode(StrEnum):
    DENSE = "dense"
    TEN_PERCENT_SPARSE = "ten_percent_sparse"


class CorruptedClientAttack(StrEnum):
    BASIS_ROTATION = "basis_rotation"
    FALSE_RANK_REPORTING = "false_rank_reporting"
    BETA_UNDER_REPORTING = "beta_under_reporting"
    TRANSITION_POISONING = "transition_poisoning"
    FABRICATED_COMPLEMENTARITY = "fabricated_complementarity"


class SyntheticCorruptionAttack(StrEnum):
    ROTATION = "rotation"
    RANK_MISREPORT = "rank_misreport"
    BETA_UNDERREPORT = "beta_underreport"
    POISONING = "poisoning"
    FABRICATED_COMPLEMENTARITY = "fabricated_complementarity"


class ExclusionReason(StrEnum):
    CONFLICTING_DUPLICATE = "CONFLICTING_DUPLICATE"
    MALFORMED_RECORD = "MALFORMED_RECORD"
    NONFINITE_FEATURE = "NONFINITE_FEATURE"
    MISSING_SAMPLE_IDENTITY = "MISSING_SAMPLE_IDENTITY"
    MISSING_CHRONOLOGY = "MISSING_CHRONOLOGY"
    MISSING_BINARY_LABEL = "MISSING_BINARY_LABEL"
    LABEL_VT_COUNT_CONFLICT = "LABEL_VT_COUNT_CONFLICT"
    LOW_VARIANCE_FEATURE = "LOW_VARIANCE_FEATURE"
    VALIDATION_STRATUM_TOO_SMALL = "VALIDATION_STRATUM_TOO_SMALL"


class EligibilityStatus(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    OPERATOR_INELIGIBLE = "operator_ineligible"


class ClientSemanticsClass(StrEnum):
    NATURAL_ORGANIZATION = "natural-organization"
    NATURAL_SOURCE = "natural-source"
    DIAGNOSTIC_PARTITION = "diagnostic-partition"
    CORPUS_LEVEL_CLIENT = "corpus-level-client"


class DatasetEligibilityRole(StrEnum):
    PRIMARY_EVIDENCE = "eligible-for-primary-evidence"
    SECONDARY_EVIDENCE = "eligible-for-secondary-evidence"
    DIAGNOSTIC_ONLY = "diagnostic-only"
    UNUSABLE = "unusable-for-the-intended-evidence"


class FeasibilityCondition(StrEnum):
    CHRONOLOGY_VALID = "chronology-valid"
    MALICIOUS_HISTORY_SUFFICIENT = "malicious-history-sufficient"
    CONTROLS_SUFFICIENT = "controls-sufficient"
    CONTEXT_FIELDS_OBSERVED = "required-context-fields-observed"
    COHORTS_CUTOFF_SAFE = "cohorts-cutoff-safe"
    OPERATOR_ARTIFACTS_AVAILABLE = "raw-operator-artifacts-available"
    REPRESENTATION_TRAINABLE_WITHOUT_LEAKAGE = "representation-trainable-without-leakage"


class HorizonAvailability(StrEnum):
    OBSERVABLE = "OBSERVABLE"
    MISSING_SOURCE_DATA = "MISSING_SOURCE_DATA"


class AbstentionReason(StrEnum):
    ABSTAIN_NO_USABLE_CONTROL = "ABSTAIN_NO_USABLE_CONTROL"
    ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT = "ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT"
    ABSTAIN_INSUFFICIENT_CONTROL_SUPPORT = "ABSTAIN_INSUFFICIENT_CONTROL_SUPPORT"
    ABSTAIN_INSUFFICIENT_PRIVATE_ALLOWANCE_HISTORY = (
        "ABSTAIN_INSUFFICIENT_PRIVATE_ALLOWANCE_HISTORY"
    )
    ABSTAIN_UNSTABLE_NUISANCE_RANK = "ABSTAIN_UNSTABLE_NUISANCE_RANK"
    ABSTAIN_WEAK_EIGENGAP = "ABSTAIN_WEAK_EIGENGAP"
    ABSTAIN_CONTROL_RECONSTRUCTION_FAILURE = "ABSTAIN_CONTROL_RECONSTRUCTION_FAILURE"
    ABSTAIN_FEASIBLE_SET_INCONSISTENT = "ABSTAIN_FEASIBLE_SET_INCONSISTENT"
    ABSTAIN_INSUFFICIENT_TEMPORAL_HISTORY = "ABSTAIN_INSUFFICIENT_TEMPORAL_HISTORY"
    ABSTAIN_FORECAST_SET_TOO_WIDE = "ABSTAIN_FORECAST_SET_TOO_WIDE"
    ABSTAIN_NO_CERTIFIED_ACTION = "ABSTAIN_NO_CERTIFIED_ACTION"
    ABSTAIN_OPERATOR_COVERAGE_INSUFFICIENT = "ABSTAIN_OPERATOR_COVERAGE_INSUFFICIENT"
    ABSTAIN_SYNCHRONIZED_NUISANCE_RISK = "ABSTAIN_SYNCHRONIZED_NUISANCE_RISK"
    ABSTAIN_SINGLE_CLIENT_CERTIFICATE_DOMINANCE = "ABSTAIN_SINGLE_CLIENT_CERTIFICATE_DOMINANCE"


NonNegativeInt = Annotated[
    int,
    Field(ge=0, strict=True),
]
PositiveInt = Annotated[
    int,
    Field(gt=0, strict=True),
]
SignedInt = Annotated[
    int,
    Field(strict=True),
]

FiniteFloat = Annotated[
    float,
    Field(allow_inf_nan=False),
]
NonNegativeFloat = Annotated[
    float,
    Field(ge=0, allow_inf_nan=False),
]
PositiveFloat = Annotated[
    float,
    Field(gt=0, allow_inf_nan=False),
]
UnitInterval = Annotated[
    float,
    Field(ge=0.0, le=1.0, allow_inf_nan=False),
]
OpenUnitInterval = Annotated[
    float,
    Field(gt=0.0, lt=1.0, allow_inf_nan=False),
]

NonEmptyString = Annotated[
    str,
    Field(strict=True),
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
    ),
]
StrictBoolean = Annotated[
    bool,
    Field(strict=True),
]
StrictBytes = Annotated[
    bytes,
    Field(strict=True),
]


SampleCount = NonNegativeInt
ClientCount = NonNegativeInt
ClientIndex = NonNegativeInt
EvaluationCount = NonNegativeInt
ReplicateIndex = NonNegativeInt
RoundCount = NonNegativeInt
EpochIndex = NonNegativeInt
RankDimension = PositiveInt
DimensionValue = PositiveInt
DetectionCount = NonNegativeInt
MinimumDetectionCount = PositiveInt
SupportThreshold = PositiveInt
MonthIndex = NonNegativeInt
IterationCount = NonNegativeInt
HorizonStep = NonNegativeInt
CatchUpStep = NonNegativeInt
WindowMonth = NonNegativeInt
UsageCount = NonNegativeInt
UnitCount = NonNegativeInt
OrderIndex = NonNegativeInt
DrawIndex = NonNegativeInt
ResampleCount = PositiveInt
WindowSpanMonths = PositiveInt
HorizonMonths = PositiveInt
PairedCutoffCount = PositiveInt
CutoffCount = NonNegativeInt
PairCount = PositiveInt
ActionCount = NonNegativeInt
SelectedCount = PositiveInt
MaximumIterations = PositiveInt
PercentileValue = Annotated[int, Field(ge=0, le=100)]


Probability = UnitInterval
Fraction = UnitInterval
MetricRate = UnitInterval
Quantile = UnitInterval
CoverageLevel = UnitInterval
SignificanceLevel = UnitInterval
ConfidenceLevel = UnitInterval
BootstrapAlpha = Annotated[float, Field(gt=0.0, le=0.5, allow_inf_nan=False)]
ScalarCoefficient = Annotated[
    float,
    Field(gt=0.0, le=1.0, allow_inf_nan=False),
]
PercentagePoints = NonNegativeFloat
AngleDegrees = Annotated[float, Field(ge=0.0, le=360.0)]
VarianceThreshold = NonNegativeFloat
StandardizationFloor = PositiveFloat
LearningRate = PositiveFloat
BatchSize = PositiveInt
RidgeLambda = PositiveFloat
Tolerance = PositiveFloat
KurtosisExcess = PositiveFloat
SensitivityMultiplier = PositiveFloat
EffectiveSampleSize = PositiveFloat
Sigma = PositiveFloat
TimeoutSeconds = PositiveFloat
Epsilon = PositiveFloat
ZeroDisplacementFloor = PositiveFloat
ConditionNumberLimit = PositiveFloat
EpochCount = PositiveInt
SampleSize = PositiveInt
DrawCount = PositiveInt
ReferenceCenterCount = PositiveInt
ReplicateCount = PositiveInt
EventCount = PositiveInt
FederationClientCount = PositiveInt
IntersectionDimension = NonNegativeInt
RankIncrement = PositiveInt
BudgetAmount = NonNegativeFloat

LossValue = FiniteFloat
ActionScore = FiniteFloat
LogDeterminantGain = FiniteFloat
LogitValue = FiniteFloat
ProbabilityValue = UnitInterval
NormValue = NonNegativeFloat
UncertaintyRadius = NonNegativeFloat
CoordinateValue = FiniteFloat
IntervalBound = FiniteFloat
DegradationValue = FiniteFloat
ThresholdValue = FiniteFloat
EpochSeconds = FiniteFloat
EigengapRatio = PositiveFloat
SimilarityScore = UnitInterval
ParameterValue = FiniteFloat
PValue = UnitInterval
RankBiserialEffectSize = Annotated[float, Field(ge=-1.0, le=1.0)]
CutoffDifferenceValue = FiniteFloat
TestStatisticValue = FiniteFloat
FeatureValue = FiniteFloat
DisplacementComponent = FiniteFloat
ObservedValue = NonEmptyString
EmbeddingComponent = FiniteFloat


ActionDecision = NonEmptyString
ExecutionReason = NonEmptyString
WorkflowStatus = NonEmptyString
DiagnosisMessage = NonEmptyString
WorkflowDescription = NonEmptyString
DetailMessage = NonEmptyString
OperationalizationText = NonEmptyString
RuleDescription = NonEmptyString
NormalizedOperatorFormText = NonEmptyString
ArtifactName = NonEmptyString
ToolchainIdentifier = NonEmptyString
TableIdentifier = NonEmptyString
FigureIdentifier = NonEmptyString
ComparatorIdentifier = NonEmptyString
RoadmapSectionId = NonEmptyString
ParameterName = NonEmptyString
ManifestFieldName = NonEmptyString
IntegrityCheckName = NonEmptyString
ScientificInvariantName = NonEmptyString
CohortIdentifier = NonEmptyString
OperatorIdentifier = NonEmptyString
FamilyName = NonEmptyString
AblationIdentifier = NonEmptyString
ProducerIdentifier = NonEmptyString
RequirementId = NonEmptyString
DatasetName = NonEmptyString
FieldName = NonEmptyString
GridCellLabel = NonEmptyString
LoggerName = NonEmptyString
HashDigest = NonEmptyString
ModuleQualifiedName = NonEmptyString
SourceText = NonEmptyString
VersionText = NonEmptyString
CalendarMonthString = Annotated[
    str,
    Field(strict=True),
    StringConstraints(
        strip_whitespace=True,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    ),
]
CommitHash = Annotated[
    str,
    Field(strict=True),
    StringConstraints(
        strip_whitespace=True,
        pattern=r"^[0-9a-fA-F]{7,64}$",
    ),
]
RelativePosixPath = Annotated[
    str,
    StringConstraints(pattern=r"^[A-Za-z0-9][A-Za-z0-9_\-./]*$"),
]


ValidationFlag = StrictBoolean
DomainValidityFlag = StrictBoolean
CertificationFlag = StrictBoolean
AmbiguityFlag = StrictBoolean
AbstentionFlag = StrictBoolean
BinaryLabel = StrictBoolean
EligibilityFlag = StrictBoolean
OptionalFlag = StrictBoolean
OverwriteRequested = StrictBoolean
DataAvailabilityFlag = StrictBoolean
ActivationFlag = StrictBoolean
PassingFlag = StrictBoolean
OverlapFlag = StrictBoolean
ObservabilityFlag = StrictBoolean
SufficiencyFlag = StrictBoolean
ProhibitionFlag = StrictBoolean
MaliciousnessFlag = StrictBoolean
IdentifiabilityFlag = StrictBoolean
MonotonicityFlag = StrictBoolean
CorrectnessFlag = StrictBoolean
BoundValidityFlag = StrictBoolean
NonIdentifiabilityFlag = StrictBoolean
TriggerabilityFlag = StrictBoolean
GateComplianceFlag = StrictBoolean
StabilityFlag = StrictBoolean
ContainmentFlag = StrictBoolean
SatisfactionFlag = StrictBoolean
DegeneracyFlag = StrictBoolean
ConfirmatoryFlag = StrictBoolean
ZeroExclusionFlag = StrictBoolean
MatchedTotalSamplesFlag = StrictBoolean
ExactDistributionFlag = StrictBoolean
CorrectionAppliedFlag = StrictBoolean
RejectionFlag = StrictBoolean
VerificationFlag = StrictBoolean
CertificationStatusFlag = StrictBoolean
AmbiguityStatusFlag = StrictBoolean
AbstentionStatusFlag = StrictBoolean
MechanismValidFlag = StrictBoolean


JsonEncodableValue = JsonValue
FilePath = Path
RawPayloadBytes = StrictBytes


DependencyFingerprint = NewType("DependencyFingerprint", str)
ContentChecksum = NewType("ContentChecksum", str)
RepositoryCommit = NewType("RepositoryCommit", str)
DatasetIdentity = NewType("DatasetIdentity", str)
PreprocessingIdentity = NewType("PreprocessingIdentity", str)
SplitCutoffIdentity = NewType("SplitCutoffIdentity", str)
CohortDefinition = NewType("CohortDefinition", str)
SampleIdentifier = NewType("SampleIdentifier", str)
OperatorLibraryIdentity = NewType("OperatorLibraryIdentity", str)
SolverOutcomeRecord = NewType("SolverOutcomeRecord", str)
RunResultSummary = NewType("RunResultSummary", str)
ExperimentName = NewType("ExperimentName", str)
LogNamespace = NewType("LogNamespace", str)
ClientIdentifier = NewType("ClientIdentifier", str)
SeedValue = NonNegativeInt
ExperimentDirectoryName = NonEmptyString

__all__ = [
    "AblationIdentifier",
    "AbstentionFlag",
    "AbstentionReason",
    "ActionCount",
    "ActionScore",
    "ActionDecision",
    "ActivationFlag",
    "AmbiguityFlag",
    "AmbiguityStatusFlag",
    "AngleDegrees",
    "ArtifactBoundary",
    "ArtifactName",
    "ArtifactVerificationStatus",
    "BatchSize",
    "BootstrapAlpha",
    "BinaryLabel",
    "BoundValidityFlag",
    "BudgetAmount",
    "CalendarMonthString",
    "CertificationFlag",
    "CertificationStatus",
    "CertificationStatusFlag",
    "ClientCount",
    "ClientIdentifier",
    "ClientIndex",
    "ClientSemanticsClass",
    "CohortDefinition",
    "CohortIdentifier",
    "CommitHash",
    "ConditionNumberLimit",
    "ConfidenceLevel",
    "ConfirmatoryFlag",
    "ConfirmatoryFormat",
    "ContainmentFlag",
    "ContentChecksum",
    "CoordinateValue",
    "CorrectionAppliedFlag",
    "CorrectnessFlag",
    "CorruptedClientAttack",
    "CoverageLevel",
    "CutoffCount",
    "CutoffDifferenceValue",
    "DataAvailabilityFlag",
    "DatasetEligibilityRole",
    "DatasetIdentity",
    "DatasetName",
    "DatasetSelector",
    "DegeneracyFlag",
    "DegradationValue",
    "DependencyFingerprint",
    "DetailMessage",
    "DetectionCount",
    "DiagnosisMessage",
    "DimensionValue",
    "DisplacementComponent",
    "DomainValidityFlag",
    "DrawCount",
    "DrawIndex",
    "EffectDirection",
    "EffectiveSampleSize",
    "EigengapRatio",
    "EligibilityFlag",
    "EligibilityStatus",
    "EmbeddingComponent",
    "EpochCount",
    "EpochSeconds",
    "EpochIndex",
    "Epsilon",
    "EvaluationCount",
    "EventCount",
    "ExactDistributionFlag",
    "ExclusionReason",
    "ExecutableWorkflowName",
    "ExecutionReason",
    "ExperimentDirectoryName",
    "ExperimentName",
    "FamilyName",
    "FeasibilityCondition",
    "FeatureValue",
    "FigureIdentifier",
    "FederationClientCount",
    "FederationGeometry",
    "FieldName",
    "FilePath",
    "Fraction",
    "GateComplianceFlag",
    "GridCellLabel",
    "HashDigest",
    "HorizonAvailability",
    "HorizonMonths",
    "HorizonStep",
    "IdentifiabilityFlag",
    "IntegrityCheckName",
    "IntersectionDimension",
    "IntervalBound",
    "IterationCount",
    "JsonEncodableValue",
    "KurtosisExcess",
    "LearningRate",
    "LogNamespace",
    "LogDeterminantGain",
    "LoggerName",
    "LogitValue",
    "LossValue",
    "MaliciousnessFlag",
    "ManifestFieldName",
    "MatchedTotalSamplesFlag",
    "MaximumIterations",
    "MechanismValidFlag",
    "MetricRate",
    "MinimumDetectionCount",
    "MissingCutoffReason",
    "ModuleQualifiedName",
    "MonotonicityFlag",
    "MonthIndex",
    "NonEmptyString",
    "NonIdentifiabilityFlag",
    "NormValue",
    "NormalizedOperatorFormText",
    "ObservabilityFlag",
    "OperationalizationText",
    "OperatorIdentifier",
    "OperatorLibraryIdentity",
    "OptionalFlag",
    "OrderIndex",
    "OverlapFlag",
    "OverwriteRequested",
    "PValue",
    "PairCount",
    "PairedCutoffCount",
    "ParameterName",
    "ParameterValue",
    "PassingFlag",
    "PercentagePoints",
    "PercentileValue",
    "PositiveInt",
    "PreprocessingIdentity",
    "PrivateTransitionSparsityMode",
    "Probability",
    "ProducerIdentifier",
    "ProhibitionFlag",
    "Quantile",
    "RankBiserialEffectSize",
    "RankDimension",
    "RankIncrement",
    "RankSelectionMethod",
    "RawPayloadBytes",
    "ReferenceCenterCount",
    "RelativePosixPath",
    "ReplicateCount",
    "ReplicateIndex",
    "RepositoryCommit",
    "RequirementId",
    "ResampleCount",
    "RidgeLambda",
    "RoadmapSectionId",
    "RoundCount",
    "RuleDescription",
    "RunResultSummary",
    "RunnableWorkflowName",
    "SampleCount",
    "SampleIdentifier",
    "SampleSize",
    "SatisfactionFlag",
    "ScalarCoefficient",
    "ScientificAssumption",
    "ScientificInvariantName",
    "ScientificOutcome",
    "SeedValue",
    "SelectedCount",
    "SensitivityMultiplier",
    "Sigma",
    "SignificanceLevel",
    "SimilarityScore",
    "SolverOutcomeRecord",
    "SourceText",
    "SplitCutoffIdentity",
    "StabilityFlag",
    "StandardizationFloor",
    "StrictBoolean",
    "StrictBytes",
    "SufficiencyFlag",
    "SupportThreshold",
    "SyntheticCorruptionAttack",
    "ThresholdValue",
    "TimeoutSeconds",
    "Tolerance",
    "ToolchainIdentifier",
    "TableIdentifier",
    "TriggerabilityFlag",
    "UnitCount",
    "UncertaintyRadius",
    "UsageCount",
    "ValidationFlag",
    "VarianceThreshold",
    "VerificationFlag",
    "VersionText",
    "WindowMonth",
    "WindowSpanMonths",
    "WorkflowDescription",
    "WorkflowStatus",
    "ZeroDisplacementFloor",
    "ZeroExclusionFlag",
]
