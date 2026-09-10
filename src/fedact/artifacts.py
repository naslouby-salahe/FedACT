from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import NewType

from pydantic import BaseModel

from fedact.config.models import StrictModel, WorkspaceConfig
from fedact.domain.types import (
    ContentChecksum,
    DegradationValue,
    DependencyFingerprint,
    ExecutableWorkflowName,
    ExperimentName,
    HashDigest,
    JsonEncodableValue,
    MetricRate,
    ParameterName,
    RawPayloadBytes,
    RelativePosixPath,
    ScientificOutcome,
    SourceText,
)


@dataclass(frozen=True)
class WorkspaceOutputDirectories:
    preprocessing: Path
    shared_artifacts: Path
    shared_models: Path
    shared_scores: Path
    shared_fitted: Path
    shared_baselines: Path
    shared_derived: Path
    experiments: Path
    cache: Path
    staging: Path
    result_experiments: Path
    project_summary: Path
    reproducibility: Path


@dataclass(frozen=True)
class WorkspaceLayout:
    repository_root: Path
    workspace: WorkspaceConfig

    def resolve(self, relative_path: RelativePosixPath | ExperimentName) -> Path:
        return self.repository_root / relative_path

    def output_directories(self) -> WorkspaceOutputDirectories:
        directories = self.workspace.directories
        return WorkspaceOutputDirectories(
            preprocessing=self.resolve(directories.preprocessing),
            shared_artifacts=self.resolve(directories.shared_artifacts),
            shared_models=self.resolve(directories.shared_models),
            shared_scores=self.resolve(directories.shared_scores),
            shared_fitted=self.resolve(directories.shared_fitted),
            shared_baselines=self.resolve(directories.shared_baselines),
            shared_derived=self.resolve(directories.shared_derived),
            experiments=self.resolve(directories.experiments),
            cache=self.resolve(directories.cache),
            staging=self.resolve(directories.staging),
            result_experiments=self.resolve(directories.result_experiments),
            project_summary=self.resolve(directories.project_summary),
            reproducibility=self.resolve(directories.reproducibility),
        )

    def experiment_workspace(self, experiment_name: ExperimentName) -> Path:
        return self.resolve(self.workspace.directories.experiments) / experiment_name

    def result_experiment_directory(self, experiment_name: ExperimentName) -> Path:
        base = self.resolve(self.workspace.directories.result_experiments) / experiment_name
        return base

    def staging_directory(self) -> Path:
        return self.resolve(self.workspace.directories.staging)


DeterministicJsonPayload = NewType("DeterministicJsonPayload", str)
HexDigest = NewType("HexDigest", str)
ArtifactIdentity = NewType("ArtifactIdentity", str)


def deterministic_json(value: JsonEncodableValue) -> DeterministicJsonPayload:
    return DeterministicJsonPayload(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    )


def sha256_digest(payload: DeterministicJsonPayload) -> HexDigest:
    return HexDigest(f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}")


def content_checksum(content: RawPayloadBytes) -> ContentChecksum:
    return ContentChecksum(f"sha256:{hashlib.sha256(content).hexdigest()}")


@dataclass(frozen=True)
class MaterialDependency:
    name: ParameterName
    content_hash: HashDigest


def compute_dependency_fingerprint(
    dependencies: tuple[MaterialDependency, ...],
) -> DependencyFingerprint:
    ordered = sorted(dependencies, key=lambda dependency: dependency.name)
    names = [dependency.name for dependency in ordered]
    if len(set(names)) != len(names):
        raise ValueError("material dependencies contain duplicate names")
    payload = deterministic_json([{"name": d.name, "value": d.content_hash} for d in ordered])
    return DependencyFingerprint(sha256_digest(payload))


class PayloadStorageError(ValueError):
    pass


def write_bytes_atomically(destination: Path, payload: RawPayloadBytes) -> ContentChecksum:
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(f".{destination.name}.staging")
    staging.write_bytes(payload)
    os.replace(staging, destination)
    return content_checksum(payload)


def write_text_atomically(destination: Path, payload: SourceText) -> ContentChecksum:
    return write_bytes_atomically(destination, payload.encode("utf-8"))


def read_bytes(source: Path) -> RawPayloadBytes:
    if not source.is_file():
        raise PayloadStorageError(f"payload is missing: {source}")
    return source.read_bytes()


class WorkflowResultRecord(StrictModel):
    workflow: ExecutableWorkflowName
    scientific_outcome: ScientificOutcome
    mean_false_negative_rate: MetricRate | None = None
    mean_certification_rate: MetricRate | None = None
    static_chronological_false_negative_rate: MetricRate | None = None
    early_horizon_fnr_reduction_percentage_points: DegradationValue | None = None
    clean_fnr_degradation_percentage_points: DegradationValue | None = None


def workflow_result_path(experiment_directory: Path) -> Path:
    return experiment_directory / "result.json"


def workflow_evidence_path(experiment_directory: Path) -> Path:
    return experiment_directory / "evidence.json"


def write_workflow_result(experiment_directory: Path, record: WorkflowResultRecord) -> Path:
    destination = workflow_result_path(experiment_directory)
    write_text_atomically(destination, record.model_dump_json(indent=2))
    return destination


def write_workflow_evidence(experiment_directory: Path, record: WorkflowResultRecord) -> Path:
    destination = workflow_evidence_path(experiment_directory)
    write_text_atomically(destination, record.model_dump_json(indent=2))
    return destination


def read_validated_json_model[ValidatedModel: BaseModel](
    source: Path, model_type: type[ValidatedModel]
) -> ValidatedModel:
    return model_type.model_validate_json(source.read_text(encoding="utf-8"))


def read_workflow_result(experiment_directory: Path) -> WorkflowResultRecord | None:
    source = workflow_result_path(experiment_directory)
    if not source.is_file():
        return None
    return read_validated_json_model(source, WorkflowResultRecord)
