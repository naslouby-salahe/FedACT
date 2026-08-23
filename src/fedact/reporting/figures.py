from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field

FigureIdentifier = Annotated[str, Field(min_length=1)]


def generate_figure_placeholder(figure_name: FigureIdentifier, output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(f"% Figure {figure_name}\n", encoding="utf-8")
