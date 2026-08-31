from __future__ import annotations

from pathlib import Path

from fedact.domain.enums import ScientificOutcome
from fedact.reporting.export import (
    LatexMacroName,
    LatexMacroValue,
    generate_project_summary,
    synthesize_latex_macros,
)


def test_synthesize_latex_macros(tmp_path: Path) -> None:
    out = tmp_path / "macros.tex"
    synthesize_latex_macros(((LatexMacroName("testMacro"), LatexMacroValue("123")),), out)
    assert out.exists()
    assert "newcommand{" in out.read_text(encoding="utf-8")


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
