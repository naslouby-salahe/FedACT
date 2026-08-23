from __future__ import annotations

from pathlib import Path

from fedact.reporting.figures import generate_figure_placeholder


def test_generate_figure_placeholder(tmp_path: Path) -> None:
    out = tmp_path / "fig.tex"
    generate_figure_placeholder("fig_1", out)
    assert out.exists()
