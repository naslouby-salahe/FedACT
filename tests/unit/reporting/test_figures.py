from __future__ import annotations

from pathlib import Path

from fedact.analysis.reporting import generate_prospective_metrics_figure


def test_generate_prospective_metrics_figure(tmp_path: Path) -> None:
    out = tmp_path / "fig.png"
    generate_prospective_metrics_figure("fig_1", 0.08, 0.82, 3, out)
    assert out.is_file()
    assert out.stat().st_size > 0
