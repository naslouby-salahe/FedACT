from __future__ import annotations

import subprocess
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


class WorkflowArtifactName(StrEnum):
    ENDPOINT_FIT_CACHE = "endpoint_fit_cache.json"
    ACTIONS = "actions.json"
    CALIBRATION_OBSERVATIONS = "observations.json"
    CALIBRATION_SELECTION = "selected.json"
    CHALLENGES = "challenges.json"
    CERTIFICATE_DECISIONS = "certificate-decisions.json"
    CUTOFF_COMPARISONS = "cutoff-comparisons.json"
    CENTRAL_PATTERN = "central-pattern.json"
    IDENTIFICATION_DIAGNOSTICS = "identification-diagnostics.json"
    TEMPORAL_DYNAMICS = "temporal-dynamics.json"
    ABLATION_MEASUREMENTS = "measurements.json"
    FEDERATION_CLIENTS = "clients.json"
    EVIDENCE = "evidence.json"
    RESULT = "result.json"
    STRESS_MEASUREMENTS = "stress-measurements.json"


class CliCommandName(StrEnum):
    ACQUIRE = "acquire"
    DOCTOR = "doctor"
    PREPROCESS = "preprocess"
    PLAN = "plan"
    SMOKE = "smoke"
    RUN = "run"
    STATUS = "status"
    REPORT = "report"


class ToolchainComponent(StrEnum):
    APKTOOL = "apktool"
    APKSIGNER = "apksigner"
    AAPT2 = "aapt2"
    CLAMSCAN = "clamscan"
    KEYTOOL = "keytool"
    ZIPALIGN = "zipalign"
    UPX = "upx"
    ADB = "adb"
    AVDMANAGER = "avdmanager"
    EMULATOR = "emulator"


class SupplementarySignatureFileName(StrEnum):
    MALWARE_HASH = "malwarehash.hsb"
    ROGUE = "rogue.hdb"
    FOXHOLE_FILENAME = "foxhole_filename.cdb"
    FOXHOLE_GENERIC = "foxhole_generic.cdb"


class SupplementarySignatureArtifactName(StrEnum):
    MANIFEST = "manifest.json"


class DatasetSelector(StrEnum):
    LAMDA = "lamda"
    EMBER2024 = "ember2024"


class LamdaFeatureCategory(StrEnum):
    ACTIVITY_LIST = "ActivityList"
    BROADCAST_RECEIVER_LIST = "BroadcastReceiverList"
    SERVICE_LIST = "ServiceList"
    REQUESTED_PERMISSION_LIST = "RequestedPermissionList"
    INTENT_FILTER_LIST = "IntentFilterList"
    HARDWARE_COMPONENTS_LIST = "HardwareComponentsList"
    RESTRICTED_API_LIST = "RestrictedApiList"
    SUSPICIOUS_API_LIST = "SuspiciousApiList"
    URL_DOMAIN_LIST = "URLDomainList"
    USED_PERMISSIONS_LIST = "UsedPermissionsList"


class AndroidManifestTag(StrEnum):
    ACTIVITY = "activity"
    RECEIVER = "receiver"
    SERVICE = "service"
    ACTION = "action"
    CATEGORY = "category"


class SensitivityParameterName(StrEnum):
    CONTROL_SPAN = "rho"
    PRIVATE_CONTAMINATION = "xi"
    HISTORICAL_PLAUSIBILITY_RADIUS = "R"
    ALIGNMENT_THRESHOLD = "tau_align"
    AMBIGUITY_WIDTH = "tau_amb"
    FORECAST_HORIZON = "horizon"
    NUISANCE_RANK = "nuisance_rank"
    TARGET_COVERAGE = "coverage_level"


class FederationGeometry(StrEnum):
    REDUNDANT = "redundant"
    COMPLEMENTARY = "complementary"


class RandomMatchLevel(StrEnum):
    EXACT = "exact_action_match"
    SOURCE_SAMPLE = "source_sample_match"
    COHORT_ONLY = "cohort_only_match"


class ClientSelectionComparator(StrEnum):
    RANDOM = "random"
    LARGEST_SAMPLE_COUNT = "largest_sample_count"
    GLOBAL_INFORMATION = "global_information"
    ACTION_INTERVAL_CONTRACTION = "action_interval_contraction"


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


class RejectionStage(StrEnum):
    MALICIOUS_SUPPORT = "malicious_support"
    ENCODER = "encoder"
    POINT_ESTIMATE = "point_estimate"
    TRANSITION_SUPPORT = "transition_support"
    HISTORICAL_DIAMETER_POOL = "historical_diameter_pool"
    CLIENT_CONSTRAINT_FIT = "client_constraint_fit"


class PeOperatorFamilyName(StrEnum):
    APPEND_BENIGN_EOF_BYTES = "append-benign-eof-bytes"
    FILL_EXISTING_SECTION_SLACK = "fill-existing-section-slack"
    ADD_UNUSED_IMPORT = "add-unused-import"
    RENAME_SECTION = "rename-section"
    ADD_READ_ONLY_SECTION = "add-read-only-section"
    ENTRY_POINT_TRAMPOLINE = "entry-point-trampoline"
    REMOVE_AUTHENTICODE_DIRECTORY = "remove-authenticode-directory"
    ZERO_PE_CHECKSUM = "zero-pe-checksum"
    REMOVE_DEBUG_DIRECTORY = "remove-debug-directory"
    UPX_PACK_UNPACK = "upx-pack-unpack"


class ApkOperatorFamilyName(StrEnum):
    UNREACHABLE_BENIGN_GADGET_INJECTION = "unreachable-benign-gadget-injection"
    PERMISSION_NEUTRAL_RESOURCE_INJECTION = "permission-neutral-resource-injection"


OperatorFamilyName = PeOperatorFamilyName | ApkOperatorFamilyName


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
CorrelationCoefficient = Annotated[
    float,
    Field(ge=-1.0, le=1.0, allow_inf_nan=False),
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
FeatureValue = NewType("FeatureValue", float)
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
SubprocessEnvironment = NewType("SubprocessEnvironment", dict[str, str])
ApkFileBytes = NewType("ApkFileBytes", bytes)
PeFileBytes = NewType("PeFileBytes", bytes)
PayloadBytes = NewType("PayloadBytes", int)
FileSuffix = NewType("FileSuffix", str)
AndroZooApiKey = NewType("AndroZooApiKey", str)
ByteCount = NewType("ByteCount", int)
ByteBudget = NewType("ByteBudget", int)
NormalizedParameterString = NewType("NormalizedParameterString", str)
EmulatorProcess = NewType("EmulatorProcess", subprocess.Popen[bytes])
ArtifactIdentity = NewType("ArtifactIdentity", str)
CalendarMonth = NewType("CalendarMonth", int)
CalendarMonthCell = NewType("CalendarMonthCell", str)
CompositionLength = NewType("CompositionLength", int)
CompositionLengthLimit = NewType("CompositionLengthLimit", int)
CoverageRatio = NewType("CoverageRatio", float)
DeterministicJsonPayload = NewType("DeterministicJsonPayload", str)
EmberJsonObject = NewType("EmberJsonObject", dict[str, JsonEncodableValue])
EmberJsonObjectList = NewType("EmberJsonObjectList", list[EmberJsonObject])
EmberJsonStringList = NewType("EmberJsonStringList", list[str])
EmberJsonIntegerList = NewType("EmberJsonIntegerList", list[int])
FeatureColumnIndex = NewType("FeatureColumnIndex", int)
GridCellIdentity = NewType("GridCellIdentity", str)
IndexInPopulation = NewType("IndexInPopulation", int)
LatexTableCell = NewType("LatexTableCell", str)
MaximumMatchesPerSample = NewType("MaximumMatchesPerSample", int)
NoiseSeedIdentity = NewType("NoiseSeedIdentity", str)
OutputHash = NewType("OutputHash", str)
PeMachineCode = NewType("PeMachineCode", int)
StructuralSeedIdentity = NewType("StructuralSeedIdentity", str)
VerificationMetric = NewType("VerificationMetric", float)
WeekIdentifier = NewType("WeekIdentifier", str)
FeatureColumnPrefix = NonEmptyString
FeatureColumnName = NewType("FeatureColumnName", str)
FeatureIndex = NewType("FeatureIndex", int)
TabularColumnName = NewType("TabularColumnName", str)
ApiReference = NewType("ApiReference", str)
AndroidAvdName = NewType("AndroidAvdName", str)
AndroidDeviceSerial = NewType("AndroidDeviceSerial", str)
AndroidPackageName = NewType("AndroidPackageName", str)
AndroidSystemImage = NewType("AndroidSystemImage", str)
ApkSigningKeyAlias = NewType("ApkSigningKeyAlias", str)
ApkSigningPassword = NewType("ApkSigningPassword", str)
ApkArchiveEntryName = NewType("ApkArchiveEntryName", str)
ObservableEvent = NewType("ObservableEvent", str)
MonkeyEventCount = PositiveInt
EmulatorPort = PositiveInt
EndpointOrdinal = NonNegativeInt
ToolVersion = NewType("ToolVersion", str)
ToolchainIdentity = NewType("ToolchainIdentity", str)
PValueSeries = NewType("PValueSeries", list[float])
PValueCriterion = NewType("PValueCriterion", str)
ConfigurationHash = NewType("ConfigurationHash", str)
ConfigurationFieldName = NewType("ConfigurationFieldName", str)
ConfigurationKey = NewType("ConfigurationKey", str)
ConfigurationPayloadText = NewType("ConfigurationPayloadText", str)
ConfigurationRawMapping = NewType("ConfigurationRawMapping", dict[str, JsonEncodableValue])
SignatureAcquisitionTimestamp = NewType("SignatureAcquisitionTimestamp", str)
SignatureSourceUrl = NewType("SignatureSourceUrl", str)
LamdaFeatureName = NewType("LamdaFeatureName", str)
ManifestAttributeName = NewType("ManifestAttributeName", str)
ManifestAttributeValue = NewType("ManifestAttributeValue", str)
ManifestXmlTag = NewType("ManifestXmlTag", str)
ObservableFeatureToken = NewType("ObservableFeatureToken", str)
UrlDomain = NewType("UrlDomain", str)
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
    "AndroZooApiKey",
    "ApkFileBytes",
    "ApiReference",
    "AndroidManifestTag",
    "ActivationFlag",
    "AmbiguityFlag",
    "AmbiguityStatusFlag",
    "AngleDegrees",
    "ApkOperatorFamilyName",
    "ArtifactBoundary",
    "ArtifactIdentity",
    "ArtifactName",
    "ArtifactVerificationStatus",
    "BatchSize",
    "BootstrapAlpha",
    "BinaryLabel",
    "BoundValidityFlag",
    "BudgetAmount",
    "ByteBudget",
    "ByteCount",
    "CalendarMonth",
    "CalendarMonthCell",
    "CalendarMonthString",
    "CertificationFlag",
    "CertificationStatus",
    "CertificationStatusFlag",
    "ClientCount",
    "CliCommandName",
    "ClientIdentifier",
    "ClientIndex",
    "ClientSelectionComparator",
    "ClientSemanticsClass",
    "CohortDefinition",
    "CohortIdentifier",
    "CommitHash",
    "CompositionLength",
    "CompositionLengthLimit",
    "ConditionNumberLimit",
    "ConfidenceLevel",
    "ConfigurationHash",
    "ConfigurationFieldName",
    "ConfigurationKey",
    "ConfigurationPayloadText",
    "ConfigurationRawMapping",
    "ConfirmatoryFlag",
    "ConfirmatoryFormat",
    "ContainmentFlag",
    "ContentChecksum",
    "CoordinateValue",
    "CorrectionAppliedFlag",
    "CorrectnessFlag",
    "CorrelationCoefficient",
    "CorruptedClientAttack",
    "CoverageLevel",
    "CoverageRatio",
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
    "DeterministicJsonPayload",
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
    "EmberJsonIntegerList",
    "EmberJsonObject",
    "EmberJsonObjectList",
    "EmberJsonStringList",
    "EmulatorProcess",
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
    "FeatureColumnIndex",
    "FeatureValue",
    "FeatureColumnName",
    "FeatureIndex",
    "FeatureColumnPrefix",
    "FigureIdentifier",
    "FileSuffix",
    "FederationClientCount",
    "FederationGeometry",
    "FieldName",
    "FilePath",
    "Fraction",
    "GateComplianceFlag",
    "GridCellIdentity",
    "GridCellLabel",
    "HashDigest",
    "HorizonAvailability",
    "HorizonMonths",
    "HorizonStep",
    "IdentifiabilityFlag",
    "IndexInPopulation",
    "IntegrityCheckName",
    "IntersectionDimension",
    "IntervalBound",
    "IterationCount",
    "JsonEncodableValue",
    "KurtosisExcess",
    "LamdaFeatureCategory",
    "LamdaFeatureName",
    "LatexTableCell",
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
    "MaximumMatchesPerSample",
    "MechanismValidFlag",
    "MetricRate",
    "ManifestAttributeName",
    "ManifestAttributeValue",
    "ManifestXmlTag",
    "MinimumDetectionCount",
    "MissingCutoffReason",
    "ModuleQualifiedName",
    "MonotonicityFlag",
    "MonthIndex",
    "NoiseSeedIdentity",
    "NonEmptyString",
    "NonIdentifiabilityFlag",
    "NormValue",
    "NormalizedOperatorFormText",
    "ObservabilityFlag",
    "ObservableFeatureToken",
    "OperationalizationText",
    "NormalizedParameterString",
    "OperatorFamilyName",
    "OperatorIdentifier",
    "OperatorLibraryIdentity",
    "OptionalFlag",
    "OrderIndex",
    "OutputHash",
    "OverlapFlag",
    "OverwriteRequested",
    "PValue",
    "PairCount",
    "PairedCutoffCount",
    "ParameterName",
    "ParameterValue",
    "PassingFlag",
    "PayloadBytes",
    "PeMachineCode",
    "PeOperatorFamilyName",
    "PercentagePoints",
    "PeFileBytes",
    "PercentileValue",
    "PositiveInt",
    "PreprocessingIdentity",
    "PrivateTransitionSparsityMode",
    "Probability",
    "ProducerIdentifier",
    "ProhibitionFlag",
    "Quantile",
    "RandomMatchLevel",
    "RankBiserialEffectSize",
    "RankDimension",
    "RankIncrement",
    "RankSelectionMethod",
    "RawPayloadBytes",
    "ReferenceCenterCount",
    "RejectionStage",
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
    "ScientificAssumption",
    "ScientificInvariantName",
    "ScientificOutcome",
    "SeedValue",
    "SelectedCount",
    "SensitivityMultiplier",
    "SensitivityParameterName",
    "Sigma",
    "SignificanceLevel",
    "SimilarityScore",
    "SolverOutcomeRecord",
    "SourceText",
    "SignatureAcquisitionTimestamp",
    "SignatureSourceUrl",
    "SplitCutoffIdentity",
    "StabilityFlag",
    "StandardizationFloor",
    "StrictBoolean",
    "StrictBytes",
    "StructuralSeedIdentity",
    "SubprocessEnvironment",
    "SufficiencyFlag",
    "SupportThreshold",
    "SupplementarySignatureArtifactName",
    "SupplementarySignatureFileName",
    "SyntheticCorruptionAttack",
    "ThresholdValue",
    "TimeoutSeconds",
    "Tolerance",
    "ToolchainIdentifier",
    "TableIdentifier",
    "TabularColumnName",
    "TriggerabilityFlag",
    "UnitCount",
    "UncertaintyRadius",
    "UsageCount",
    "UrlDomain",
    "ValidationFlag",
    "VarianceThreshold",
    "VerificationFlag",
    "VerificationMetric",
    "VersionText",
    "WeekIdentifier",
    "WindowMonth",
    "WindowSpanMonths",
    "WorkflowArtifactName",
    "WorkflowDescription",
    "WorkflowStatus",
    "ZeroDisplacementFloor",
    "ZeroExclusionFlag",
]
