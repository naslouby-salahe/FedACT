from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import NewType

LatexMacroName = NewType("LatexMacroName", str)
LatexMacroValue = NewType("LatexMacroValue", str)
BACKSLASH = chr(92)


@dataclass(frozen=True)
class LatexMacro:
    name: LatexMacroName
    value: LatexMacroValue


def synthesize_latex_macros(macros: tuple[LatexMacro, ...], output_file: Path) -> None:
    lines = [
        BACKSLASH + "newcommand{" + BACKSLASH + macro.name + "}{" + macro.value + "}"
        for macro in macros
    ]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")
