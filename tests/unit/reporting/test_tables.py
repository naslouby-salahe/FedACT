from __future__ import annotations

from pathlib import Path

from fedact.reporting.tables import LatexTableCell, generate_latex_table


def test_generate_latex_table(tmp_path: Path) -> None:
    out = tmp_path / "table.tex"
    generate_latex_table(
        "t1",
        (LatexTableCell("Col1"), LatexTableCell("Col2")),
        ((LatexTableCell("A"), LatexTableCell("B")),),
        out,
    )
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "begin{table}" in content
    assert "label{tab:t1}" in content
