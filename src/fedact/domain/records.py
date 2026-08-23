from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

from fedact.domain.enums import ArtifactBoundary, WorkflowName

DependencyFingerprint = NewType("DependencyFingerprint", str)
RepositoryCommit = NewType("RepositoryCommit", str)
DatasetIdentity = NewType("DatasetIdentity", str)
PreprocessingIdentity = NewType("PreprocessingIdentity", str)
SplitCutoffIdentity = NewType("SplitCutoffIdentity", str)
CohortDefinition = NewType("CohortDefinition", str)
OperatorLibraryIdentity = NewType("OperatorLibraryIdentity", str)
SolverOutcomeRecord = NewType("SolverOutcomeRecord", str)
RunResultSummary = NewType("RunResultSummary", str)


@dataclass(frozen=True)
class WorkflowContract:
    name: WorkflowName
    scientific_purpose: str
    required_upstream_artifacts: tuple[ArtifactBoundary, ...]
    manipulations_and_comparators: str
    metrics: str
    applicable_statistical_analysis: str
    resulting_artifacts: str


@dataclass(frozen=True)
class ArtifactBoundaryContract:
    boundary: ArtifactBoundary
    reusable_artifacts: str
    consumers: tuple[ArtifactBoundary, ...]
    manuscript_only: bool = False


@dataclass(frozen=True)
class CompletionRequirements:
    required_files: frozenset[str]
    required_manifest_fields: frozenset[str]
    required_integrity_checks: frozenset[str]
    required_scientific_invariants: frozenset[str]


@dataclass(frozen=True)
class CompletionEvidence:
    present_files: frozenset[str]
    populated_manifest_fields: frozenset[str]
    passed_integrity_checks: frozenset[str]
    passed_scientific_invariants: frozenset[str]
    completion_record_committed: bool
