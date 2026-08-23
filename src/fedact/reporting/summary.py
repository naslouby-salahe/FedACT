from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from fedact.domain.types import ArtifactName, MetricRate, WorkflowStatus


@dataclass(frozen=True)
class ProjectSummaryPayload:
    project: ArtifactName
    verdict: WorkflowStatus
    prospective_fnr: MetricRate
    certification_rate: MetricRate


def generate_project_summary(metrics: ProjectSummaryPayload, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(asdict(metrics), indent=2) + chr(10), encoding="utf-8")
