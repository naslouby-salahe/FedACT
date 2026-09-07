from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field

from fedact.domain.types import MetricRate

FigureIdentifier = Annotated[str, Field(min_length=1)]
BACKSLASH = chr(92)


def generate_prospective_metrics_figure(
    figure_name: FigureIdentifier,
    mean_false_negative_rate: MetricRate,
    mean_certification_rate: MetricRate,
    output_file: Path,
) -> None:
    lines = [
        BACKSLASH + "begin{tikzpicture}",
        BACKSLASH + "begin{axis}[ybar, ymin=0, ymax=1, symbolic x coords={FNR,Certification},"
        "xtick=data, ylabel={Rate}]",
        BACKSLASH + "addplot coordinates {"
        f"(FNR,{mean_false_negative_rate}) (Certification,{mean_certification_rate})"
        "};",
        BACKSLASH + "end{axis}",
        BACKSLASH + "end{tikzpicture}",
        f"% {figure_name}",
    ]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
