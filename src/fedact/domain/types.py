from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field, JsonValue, StringConstraints

type StrictInteger = Annotated[
    int,
    Field(strict=True),
]

type NonNegativeInteger = Annotated[
    int,
    Field(ge=0, strict=True),
]

type PositiveInteger = Annotated[
    int,
    Field(gt=0, strict=True),
]

type FiniteFloat = Annotated[
    float,
    Field(allow_inf_nan=False),
]

type NonNegativeFloat = Annotated[
    float,
    Field(ge=0, allow_inf_nan=False),
]

type PositiveFloat = Annotated[
    float,
    Field(gt=0, allow_inf_nan=False),
]

type Probability = Annotated[
    float,
    Field(ge=0.0, le=1.0, allow_inf_nan=False),
]

type NonEmptyString = Annotated[
    str,
    Field(strict=True),
    StringConstraints(
        strip_whitespace=True,
        min_length=1,
    ),
]

type StrictBoolean = Annotated[
    bool,
    Field(strict=True),
]

type StrictBytes = Annotated[
    bytes,
    Field(strict=True),
]


type SampleCount = NonNegativeInteger
type EvaluationCount = NonNegativeInteger
type ReplicateIndex = NonNegativeInteger
type RoundCount = NonNegativeInteger
type EpochIndex = NonNegativeInteger

type RankDimension = PositiveInteger
type DimensionValue = PositiveInteger

type SeedValue = StrictInteger

type MonthIndex = NonNegativeInteger
type IterationCount = NonNegativeInteger
type ClientIndex = NonNegativeInteger
type HorizonStep = NonNegativeInteger
type WindowMonth = NonNegativeInteger
type UsageCount = NonNegativeInteger
type UnitCount = NonNegativeInteger
type OrderIndex = NonNegativeInteger
type DrawIndex = NonNegativeInteger

type LogLevel = StrictInteger


type LossValue = FiniteFloat
type ProbabilityValue = Probability
type LogitValue = FiniteFloat
type NormValue = NonNegativeFloat
type CoordinateValue = FiniteFloat
type MetricRate = Probability
type IntervalBound = FiniteFloat
type DegradationValue = FiniteFloat
type ThresholdValue = FiniteFloat
type EigengapRatio = NonNegativeFloat
type SimilarityScore = FiniteFloat
type TimeoutSeconds = NonNegativeFloat
type ParameterValue = FiniteFloat


type ActionDecision = NonEmptyString
type ExecutionReason = NonEmptyString
type WorkflowStatus = NonEmptyString
type DiagnosisMessage = NonEmptyString
type WorkflowDescription = NonEmptyString
type DetailMessage = NonEmptyString
type OperationalizationText = NonEmptyString
type RuleDescription = NonEmptyString
type ProvenanceText = NonEmptyString
type CanonicalFormText = NonEmptyString


type ArtifactName = NonEmptyString
type ToolchainIdentifier = NonEmptyString
type RoadmapSectionId = NonEmptyString
type ParameterName = NonEmptyString
type ManifestFieldName = NonEmptyString
type IntegrityCheckName = NonEmptyString
type ScientificInvariantName = NonEmptyString
type CohortIdentifier = NonEmptyString
type OperatorIdentifier = NonEmptyString
type FamilyName = NonEmptyString
type AblationIdentifier = NonEmptyString
type ProducerIdentifier = NonEmptyString
type RequirementId = NonEmptyString
type DatasetName = NonEmptyString
type FieldName = NonEmptyString
type GridCellLabel = NonEmptyString
type LoggerName = NonEmptyString


type HashDigest = NonEmptyString

type CommitHash = Annotated[
    str,
    Field(strict=True),
    StringConstraints(
        strip_whitespace=True,
        pattern=r"^[0-9a-fA-F]{7,64}$",
    ),
]


type CalendarMonthString = Annotated[
    str,
    Field(strict=True),
    StringConstraints(
        strip_whitespace=True,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    ),
]


type FilePath = Path
type RawPayloadBytes = StrictBytes


type ValidationFlag = StrictBoolean
type DomainValidityFlag = StrictBoolean
type CertificationFlag = StrictBoolean
type AmbiguityFlag = StrictBoolean
type AbstentionFlag = StrictBoolean
type BinaryLabel = StrictBoolean
type EligibilityFlag = StrictBoolean
type OptionalFlag = StrictBoolean


type JsonEncodableValue = JsonValue
