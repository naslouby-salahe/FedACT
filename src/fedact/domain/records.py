from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

from fedact.domain.enums import ArtifactBoundary, WorkflowName
from fedact.domain.types import (
    FilePath,
    IntegrityCheckName,
    ManifestFieldName,
    ScientificInvariantName,
    WorkflowDescription,
)

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


@dataclass(frozen=True)
class WorkflowContract:
    name: WorkflowName
    scientific_purpose: WorkflowDescription
    required_upstream_artifacts: tuple[ArtifactBoundary, ...]
    manipulations_and_comparators: WorkflowDescription
    metrics: WorkflowDescription
    applicable_statistical_analysis: WorkflowDescription
    resulting_artifacts: WorkflowDescription


@dataclass(frozen=True)
class ArtifactBoundaryContract:
    boundary: ArtifactBoundary
    reusable_artifacts: WorkflowDescription
    consumers: tuple[ArtifactBoundary, ...]
    manuscript_only: bool = False


@dataclass(frozen=True)
class BoundaryFingerprint:
    boundary: ArtifactBoundary
    dependency_fingerprint: DependencyFingerprint


@dataclass(frozen=True)
class BoundaryFingerprints:
    entries: tuple[BoundaryFingerprint, ...] = ()

    def __bool__(self) -> bool:
        return bool(self.entries)

    def for_boundary(self, boundary: ArtifactBoundary) -> DependencyFingerprint | None:
        for entry in self.entries:
            if entry.boundary is boundary:
                return entry.dependency_fingerprint
        return None


@dataclass(frozen=True)
class CompletionRequirements:
    required_files: frozenset[FilePath]
    required_manifest_fields: frozenset[ManifestFieldName]
    required_integrity_checks: frozenset[IntegrityCheckName]
    required_scientific_invariants: frozenset[ScientificInvariantName]


@dataclass(frozen=True)
class CompletionEvidence:
    present_files: frozenset[FilePath]
    populated_manifest_fields: frozenset[ManifestFieldName]
    passed_integrity_checks: frozenset[IntegrityCheckName]
    passed_scientific_invariants: frozenset[ScientificInvariantName]
    completion_record_committed: bool
