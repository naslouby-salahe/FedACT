from __future__ import annotations

from pathlib import Path

from fedact.domain.enums import ScientificOutcome
from fedact.reporting.summary import ProjectSummaryPayload, generate_project_summary


def test_generate_project_summary(tmp_path: Path) -> None:
    out = tmp_path / "summary.json"
    payload = ProjectSummaryPayload(
        project="FedACT",
        verdict=ScientificOutcome.PASS,
        prospective_fnr=0.08,
        certification_rate=0.82,
    )
    generate_project_summary(payload, out)
    assert out.exists()
    assert "FedACT" in out.read_text(encoding="utf-8")
