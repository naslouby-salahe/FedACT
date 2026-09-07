from __future__ import annotations

from pathlib import Path
from typing import Annotated, NewType

from pydantic import Field, JsonValue, StringConstraints

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
LogitValue = FiniteFloat
ProbabilityValue = UnitInterval
NormValue = NonNegativeFloat
CoordinateValue = FiniteFloat
IntervalBound = FiniteFloat
DegradationValue = FiniteFloat
ThresholdValue = FiniteFloat
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
ProvenanceText = NonEmptyString
NormalizedOperatorFormText = NonEmptyString
ArtifactName = NonEmptyString
ToolchainIdentifier = NonEmptyString
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
    "ActionCount",
    "ActionDecision",
    "ActivationFlag",
    "AmbiguityFlag",
    "AngleDegrees",
    "ArtifactName",
    "BatchSize",
    "BinaryLabel",
    "BoundValidityFlag",
    "BudgetAmount",
    "CalendarMonthString",
    "CertificationFlag",
    "ClientCount",
    "ClientIdentifier",
    "ClientIndex",
    "CohortDefinition",
    "CohortIdentifier",
    "CommitHash",
    "ConditionNumberLimit",
    "ConfidenceLevel",
    "ConfirmatoryFlag",
    "ContainmentFlag",
    "ContentChecksum",
    "CoordinateValue",
    "CorrectnessFlag",
    "CoverageLevel",
    "CutoffCount",
    "CutoffDifferenceValue",
    "DataAvailabilityFlag",
    "DatasetIdentity",
    "DatasetName",
    "DegeneracyFlag",
    "DegradationValue",
    "DependencyFingerprint",
    "DetailMessage",
    "DetectionCount",
    "DiagnosisMessage",
    "DimensionValue",
    "DomainValidityFlag",
    "DrawCount",
    "DrawIndex",
    "EigengapRatio",
    "EligibilityFlag",
    "EpochCount",
    "EpochIndex",
    "Epsilon",
    "EvaluationCount",
    "EventCount",
    "ExecutionReason",
    "ExperimentName",
    "FamilyName",
    "FederationClientCount",
    "FieldName",
    "FilePath",
    "Fraction",
    "GateComplianceFlag",
    "GridCellLabel",
    "HashDigest",
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
    "LoggerName",
    "LogitValue",
    "LossValue",
    "MaliciousnessFlag",
    "ManifestFieldName",
    "MaximumIterations",
    "MetricRate",
    "MinimumDetectionCount",
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
    "PreprocessingIdentity",
    "Probability",
    "ProducerIdentifier",
    "ProhibitionFlag",
    "ProvenanceText",
    "Quantile",
    "RankBiserialEffectSize",
    "RankDimension",
    "RankIncrement",
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
    "SampleCount",
    "SampleIdentifier",
    "SampleSize",
    "SatisfactionFlag",
    "ScalarCoefficient",
    "ScientificInvariantName",
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
    "ThresholdValue",
    "TimeoutSeconds",
    "Tolerance",
    "ToolchainIdentifier",
    "TriggerabilityFlag",
    "UnitCount",
    "UsageCount",
    "ValidationFlag",
    "VarianceThreshold",
    "VersionText",
    "WindowMonth",
    "WindowSpanMonths",
    "WorkflowDescription",
    "WorkflowStatus",
    "ZeroDisplacementFloor",
    "ZeroExclusionFlag",
]
