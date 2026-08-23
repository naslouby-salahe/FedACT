from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fedact.domain.enums import ArtifactBoundary, ExecutableWorkflowName
from fedact.domain.records import DependencyFingerprint


class SharedProducer(StrEnum):
    REPRESENTATION_DETECTOR_FIT = "representation-detector-fit"
    ENCODING_SCORING_AND_SUMMARIES = "encoding-scoring-and-summaries"
    BASELINE_FIT_PARITY = "baseline-fit-parity"
    NESTED_PRE_CUTOFF_CALIBRATION = "nested-pre-cutoff-calibration"


@dataclass(frozen=True)
class ProducerOwnership:
    producer: SharedProducer
    invoked_when: str
    owned_artifacts: str
    reuse_scope: str
    owning_command: ExecutableWorkflowName


SHARED_PRODUCER_OWNERSHIP: tuple[ProducerOwnership, ...] = (
    ProducerOwnership(
        producer=SharedProducer.REPRESENTATION_DETECTOR_FIT,
        invoked_when=(
            "a real-data workflow or representation audit first requires a missing/stale "
            "retraining-cadence checkpoint"
        ),
        owned_artifacts=(
            "cutoff-fixed representation and base-detector checkpoints plus training manifest"
        ),
        reuse_scope="every compatible monthly cutoff/workflow under §9.5",
        owning_command=ExecutableWorkflowName.PREPROCESS,
    ),
    ProducerOwnership(
        producer=SharedProducer.ENCODING_SCORING_AND_SUMMARIES,
        invoked_when=(
            "a downstream workflow first requires scores, encodings, transitions, nuisance "
            "inputs, or action displacements"
        ),
        owned_artifacts=(
            "encoded/scored observations, transition/control summaries, reusable action "
            "displacements"
        ),
        reuse_scope=(
            "workflows with the same checkpoint, samples/splits, controls/operators, and "
            "producer fingerprint"
        ),
        owning_command=ExecutableWorkflowName.PREPROCESS,
    ),
    ProducerOwnership(
        producer=SharedProducer.BASELINE_FIT_PARITY,
        invoked_when="a required comparator is first needed",
        owned_artifacts="baseline checkpoints, parity manifests, reusable baseline scores",
        reuse_scope="every compatible downstream comparison",
        owning_command=ExecutableWorkflowName.BASELINE_PARITY,
    ),
    ProducerOwnership(
        producer=SharedProducer.NESTED_PRE_CUTOFF_CALIBRATION,
        invoked_when="a dataset/cutoff first requires calibrated values",
        owned_artifacts="selected calibration result and calibrated set/model parameters",
        reuse_scope="every compatible downstream workflow at that dataset/cutoff",
        owning_command=ExecutableWorkflowName.NESTED_CALIBRATION,
    ),
)

OWNERSHIP_BY_PRODUCER: dict[SharedProducer, ProducerOwnership] = {
    entry.producer: entry for entry in SHARED_PRODUCER_OWNERSHIP
}


def ownership_for(producer: SharedProducer) -> ProducerOwnership:
    return OWNERSHIP_BY_PRODUCER[producer]


PREPROCESS_OWNED_BOUNDARIES: tuple[ArtifactBoundary, ...] = (
    ArtifactBoundary.DATASET_PREPARATION,
    ArtifactBoundary.PREPROCESSING_AND_SPLITS,
)

_PREPROCESS_TRIGGERABLE_PRODUCERS: frozenset[SharedProducer] = frozenset(
    {SharedProducer.REPRESENTATION_DETECTOR_FIT}
)


def is_preprocess_triggerable(producer: SharedProducer) -> bool:
    return producer in _PREPROCESS_TRIGGERABLE_PRODUCERS


@dataclass(frozen=True)
class PreprocessStagePlan:
    stage_order: int
    name: str
    boundary: ArtifactBoundary | None


PREPROCESS_STAGE_FLOW: tuple[PreprocessStagePlan, ...] = (
    PreprocessStagePlan(0, "raw discovery/checksum", ArtifactBoundary.INPUTS),
    PreprocessStagePlan(1, "canonical parsed preparation", ArtifactBoundary.DATASET_PREPARATION),
    PreprocessStagePlan(
        2, "chronology/cutoff construction", ArtifactBoundary.PREPROCESSING_AND_SPLITS
    ),
    PreprocessStagePlan(
        3, "split/client/cohort construction", ArtifactBoundary.PREPROCESSING_AND_SPLITS
    ),
    PreprocessStagePlan(4, "fitted preprocessing", ArtifactBoundary.PREPROCESSING_AND_SPLITS),
    PreprocessStagePlan(5, "real-data audits", ArtifactBoundary.PREPROCESSING_AND_SPLITS),
)


ReuseDecision = StrEnum(
    "ReuseDecision",
    {
        "REUSE": "reuse-compatible",
        "STALE": "recompute-stale-or-missing",
        "OVERWRITE": "recompute-overwrite",
    },
)


@dataclass(frozen=True)
class OverwriteRequest:
    requested: bool


def resolve_reuse_or_recompute(
    stored_fingerprint: DependencyFingerprint | None,
    expected_fingerprint: DependencyFingerprint,
    overwrite: OverwriteRequest,
) -> ReuseDecision:
    if overwrite.requested:
        return ReuseDecision.OVERWRITE
    if stored_fingerprint == expected_fingerprint:
        return ReuseDecision.REUSE
    return ReuseDecision.STALE
