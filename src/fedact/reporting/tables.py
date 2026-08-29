from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field

TableIdentifier = Annotated[str, Field(min_length=1)]
BACKSLASH = chr(92)


def generate_latex_table(
    table_id: TableIdentifier,
    headers: tuple[str, ...],
    rows: tuple[tuple[str, ...], ...],
    output_file: Path,
) -> None:
    _unused = table_id
    align = "l" * len(headers)
    lines = [
        BACKSLASH + "begin{table}[h]",
        BACKSLASH + "centering",
        BACKSLASH + "begin{tabular}{" + align + "}",
        BACKSLASH + "hline",
        " & ".join(headers) + " " + BACKSLASH + BACKSLASH,
        BACKSLASH + "hline",
    ]
    for row in rows:
        lines.append(" & ".join(row) + " " + BACKSLASH + BACKSLASH)
    lines.extend([BACKSLASH + "hline", BACKSLASH + "end{tabular}", BACKSLASH + "end{table}"])
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
