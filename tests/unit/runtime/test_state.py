from __future__ import annotations

import pytest

from fedact.artifacts.identity import ArtifactIdentity, ContentChecksum
from fedact.config.loading import ConfigurationHash
from fedact.domain.enums import ScientificOutcome
from fedact.runtime.state import (
    WorkflowCompletionError,
    WorkflowCompletionEvidence,
    validate_workflow_completion,
)

PRIMARY_CONFIGURATION_HASH = ConfigurationHash("sha256:" + "1" * 64)
DIAGNOSTIC_EVIDENCE_CHECKSUM = ContentChecksum("sha256:" + "3" * 64)
MANDATORY_OUTPUT_IDENTITY = ArtifactIdentity("sha256:" + "2" * 64)


def evidence(
    workflow_provenance_present: bool = True,
    configuration_hash: ConfigurationHash | None = PRIMARY_CONFIGURATION_HASH,
    run_configuration_hashes: tuple[ConfigurationHash, ...] = (PRIMARY_CONFIGURATION_HASH,),
    seed_streams_recorded: bool = True,
    mandatory_outputs_present: frozenset[ArtifactIdentity] = frozenset({MANDATORY_OUTPUT_IDENTITY}),
    required_output_identities: frozenset[ArtifactIdentity] = frozenset(
        {MANDATORY_OUTPUT_IDENTITY}
    ),
    metrics_validate: bool = True,
    scientific_outcome: ScientificOutcome = ScientificOutcome.FAIL,
    diagnostic_evidence_checksum: ContentChecksum | None = DIAGNOSTIC_EVIDENCE_CHECKSUM,
) -> WorkflowCompletionEvidence:
    assert configuration_hash is not None
    return WorkflowCompletionEvidence(
        workflow_provenance_present=workflow_provenance_present,
        configuration_hash=configuration_hash,
        run_configuration_hashes=run_configuration_hashes,
        seed_streams_recorded=seed_streams_recorded,
        mandatory_outputs_present=mandatory_outputs_present,
        required_output_identities=required_output_identities,
        metrics_validate=metrics_validate,
        scientific_outcome=scientific_outcome,
        diagnostic_evidence_checksum=diagnostic_evidence_checksum,
    )


def test_complete_evidence_passes() -> None:
    validate_workflow_completion(evidence())


def test_missing_provenance_blocks_completion() -> None:
    with pytest.raises(WorkflowCompletionError, match="provenance"):
        validate_workflow_completion(evidence(workflow_provenance_present=False))


def test_configuration_hash_must_be_whole_run_consistent() -> None:
    mutated = evidence(run_configuration_hashes=(ConfigurationHash("sha256:" + "4" * 64),))
    with pytest.raises(WorkflowCompletionError, match="configuration hash"):
        validate_workflow_completion(mutated)


def test_missing_seed_streams_block_completion() -> None:
    with pytest.raises(WorkflowCompletionError, match="seed"):
        validate_workflow_completion(evidence(seed_streams_recorded=False))


def test_missing_mandatory_outputs_block_completion() -> None:
    with pytest.raises(WorkflowCompletionError, match="mandatory outputs"):
        validate_workflow_completion(
            evidence(mandatory_outputs_present=frozenset[ArtifactIdentity]())
        )


def test_invalid_metrics_block_completion() -> None:
    with pytest.raises(WorkflowCompletionError, match="metrics"):
        validate_workflow_completion(evidence(metrics_validate=False))


def test_non_success_outcomes_require_diagnostic_evidence() -> None:
    with pytest.raises(WorkflowCompletionError, match="diagnostic"):
        validate_workflow_completion(evidence(diagnostic_evidence_checksum=None))


def test_pass_outcomes_do_not_require_diagnostic_evidence() -> None:
    validate_workflow_completion(
        evidence(scientific_outcome=ScientificOutcome.PASS, diagnostic_evidence_checksum=None)
    )
