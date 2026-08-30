from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fedact.artifacts.identity import ArtifactIdentity, ContentChecksum
from fedact.config.loading import ConfigurationHash
from fedact.domain.enums import ExecutableWorkflowName, ScientificOutcome


class WorkflowExecutionState(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    BLOCKED = "BLOCKED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INVALID = "INVALID"


@dataclass(frozen=True)
class WorkflowOutcomeRecord:
    workflow: ExecutableWorkflowName
    outcome: ScientificOutcome


type WorkflowOutcomeHistory = tuple[WorkflowOutcomeRecord, ...]


def outcome_for_workflow(
    history: WorkflowOutcomeHistory, workflow: ExecutableWorkflowName
) -> ScientificOutcome | None:
    for record in history:
        if record.workflow is workflow:
            return record.outcome
    return None


def workflows_with_recorded_outcomes(
    history: WorkflowOutcomeHistory,
) -> frozenset[ExecutableWorkflowName]:
    return frozenset(record.workflow for record in history)


class ArtifactExecutionState(StrEnum):
    STAGING = "STAGING"
    COMPLETE = "COMPLETE"
    STALE = "STALE"
    INVALID = "INVALID"


@dataclass(frozen=True)
class WorkflowCompletionEvidence:
    workflow_provenance_present: bool
    configuration_hash: ConfigurationHash | None
    run_configuration_hashes: tuple[ConfigurationHash, ...]
    seed_streams_recorded: bool
    mandatory_outputs_present: frozenset[ArtifactIdentity]
    required_output_identities: frozenset[ArtifactIdentity]
    metrics_validate: bool
    scientific_outcome: ScientificOutcome
    diagnostic_evidence_checksum: ContentChecksum | None


class WorkflowCompletionError(ValueError):
    pass


def validate_workflow_completion(
    evidence: WorkflowCompletionEvidence,
) -> None:
    if not evidence.workflow_provenance_present:
        raise WorkflowCompletionError(
            "workflow completion requires valid provenance for every internal run"
        )
    if evidence.configuration_hash is None:
        raise WorkflowCompletionError("workflow completion requires the configuration hash")
    if any(
        run_hash != evidence.configuration_hash for run_hash in evidence.run_configuration_hashes
    ):
        raise WorkflowCompletionError(
            "every internal run must record the whole-run configuration hash"
        )
    if not evidence.seed_streams_recorded:
        raise WorkflowCompletionError("workflow completion requires locked seed streams")
    missing_outputs = sorted(
        evidence.required_output_identities - evidence.mandatory_outputs_present,
        key=str,
    )
    if missing_outputs:
        raise WorkflowCompletionError(
            f"workflow completion missing mandatory outputs: {missing_outputs}"
        )
    if not evidence.metrics_validate:
        raise WorkflowCompletionError("workflow completion requires validating metrics")
    non_success = evidence.scientific_outcome is not ScientificOutcome.PASS
    if non_success and evidence.diagnostic_evidence_checksum is None:
        raise WorkflowCompletionError("non-success scientific outcomes require diagnostic evidence")
