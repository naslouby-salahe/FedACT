from __future__ import annotations

from pathlib import Path

from fedact.reporting.tables import generate_latex_table


def test_generate_latex_table(tmp_path: Path) -> None:
    out = tmp_path / "table.tex"
    generate_latex_table("t1", ("Col1", "Col2"), (("A", "B"),), out)
    assert out.exists()
    assert "begin{table}" in out.read_text(encoding="utf-8")
