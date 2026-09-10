from __future__ import annotations

from pathlib import Path

from fedact.analysis.reporting import generate_project_summary
from fedact.domain.types import ScientificOutcome


def test_generate_project_summary(tmp_path: Path) -> None:
    out = tmp_path / "summary.json"
    generate_project_summary(
        project="FedACT",
        verdict=ScientificOutcome.PASS,
        prospective_fnr=0.08,
        certification_rate=0.82,
        output_file=out,
    )
    assert out.exists()
    assert "FedACT" in out.read_text(encoding="utf-8")
