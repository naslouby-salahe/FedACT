from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from pydantic import Field

from fedact.artifacts.identity import (
    ArtifactIdentity,
    ContentChecksum,
    EnvironmentFingerprint,
    ProducerCodeFingerprint,
)
from fedact.config.loading import ConfigurationHash
from fedact.domain.enums import ScientificOutcome, WorkflowName
from fedact.domain.records import (
    CohortDefinition,
    DatasetIdentity,
    OperatorLibraryIdentity,
    PreprocessingIdentity,
    RepositoryCommit,
    RunResultSummary,
    SolverOutcomeRecord,
    SplitCutoffIdentity,
)


class ProvenanceContractError(ValueError):
    pass


PositiveHorizonMonths = Annotated[int, Field(gt=0)]


@dataclass(frozen=True)
class RunProvenance:
    workflow_name: WorkflowName
    configuration_hash: ConfigurationHash
    repository_commit: RepositoryCommit
    dataset_identity: DatasetIdentity | None = None
    raw_checksum: ContentChecksum | None = None
    preprocessing_identity: PreprocessingIdentity | None = None
    split_and_cutoff_identity: SplitCutoffIdentity | None = None
    client_cohort_definition: CohortDefinition | None = None
    horizon_months: PositiveHorizonMonths | None = None
    representation_checkpoint_hash: ContentChecksum | None = None
    detector_checkpoint_hash: ContentChecksum | None = None
    seed_streams: tuple[str, ...] = ()
    upstream_artifact_identities: tuple[ArtifactIdentity, ...] = ()
    operator_library_identity: OperatorLibraryIdentity | None = None
    solver_outcome: SolverOutcomeRecord | None = None
    producer_code_fingerprint: ProducerCodeFingerprint | None = None
    environment_fingerprint: EnvironmentFingerprint | None = None
    scientific_outcome: ScientificOutcome | None = None
    run_result: RunResultSummary | None = None
