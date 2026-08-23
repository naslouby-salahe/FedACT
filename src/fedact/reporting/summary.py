from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectSummaryPayload:
    project: str
    verdict: str
    prospective_fnr: float
    certification_rate: float


def generate_project_summary(metrics: ProjectSummaryPayload, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(asdict(metrics), indent=2) + chr(10), encoding="utf-8")
