from __future__ import annotations

from pathlib import Path

from fedact.reporting.figures import generate_prospective_metrics_figure


def test_generate_prospective_metrics_figure(tmp_path: Path) -> None:
    out = tmp_path / "fig.tex"
    generate_prospective_metrics_figure("fig_1", 0.08, 0.82, out)
    content = out.read_text(encoding="utf-8")
    assert "0.08" in content
    assert "0.82" in content
