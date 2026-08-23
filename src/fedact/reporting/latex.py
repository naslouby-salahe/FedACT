from __future__ import annotations

from pathlib import Path

BACKSLASH = chr(92)


def synthesize_latex_macros(macros: dict[str, str], output_file: Path) -> None:
    lines = [BACKSLASH + "newcommand{" + BACKSLASH + k + "}{" + v + "}" for k, v in macros.items()]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
