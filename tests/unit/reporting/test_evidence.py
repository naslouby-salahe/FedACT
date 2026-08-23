from __future__ import annotations

from pathlib import Path

from fedact.reporting.evidence import EvidenceArtifactRecord, package_evidence_index


def test_package_evidence_index(tmp_path: Path) -> None:
    out = tmp_path / "evidence.json"
    records = [EvidenceArtifactRecord(artifact="a.tex", status="verified")]
    package_evidence_index(records, out)
    assert out.exists()
    assert "a.tex" in out.read_text(encoding="utf-8")
