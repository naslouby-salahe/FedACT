from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from fedact.config.models import StrictModel
from fedact.domain.enums import ExecutableWorkflowName, ScientificOutcome
from fedact.domain.records import DegradationValue, MetricRate
from fedact.storage.checkpoints import write_text_atomically


class WorkflowResultRecord(StrictModel):
    workflow: ExecutableWorkflowName
    scientific_outcome: ScientificOutcome
    mean_false_negative_rate: MetricRate | None = None
    mean_certification_rate: MetricRate | None = None
    clean_fnr_degradation_percentage_points: DegradationValue | None = None


def workflow_result_path(experiment_directory: Path) -> Path:
    return experiment_directory / "result.json"


def write_workflow_result(experiment_directory: Path, record: WorkflowResultRecord) -> Path:
    destination = workflow_result_path(experiment_directory)
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
