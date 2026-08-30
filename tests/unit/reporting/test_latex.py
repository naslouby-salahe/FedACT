from __future__ import annotations

from pathlib import Path

from fedact.reporting.latex import (
    LatexMacro,
    LatexMacroName,
    LatexMacroValue,
    synthesize_latex_macros,
)


def test_synthesize_latex_macros(tmp_path: Path) -> None:
    out = tmp_path / "macros.tex"
    synthesize_latex_macros(
        (LatexMacro(name=LatexMacroName("testMacro"), value=LatexMacroValue("123")),), out
    )
    assert out.exists()
    assert "newcommand{" in out.read_text(encoding="utf-8")
