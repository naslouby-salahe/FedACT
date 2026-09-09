from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Annotated, NewType

from pydantic import Field

from fedact.artifacts import WorkflowResultRecord
from fedact.domain.types import (
    ArtifactName,
    ArtifactVerificationStatus,
    MetricRate,
    ScientificOutcome,
)

TableIdentifier = Annotated[str, Field(min_length=1)]
LatexTableCell = NewType("LatexTableCell", str)
BACKSLASH = chr(92)


def generate_latex_table(
    table_id: TableIdentifier,
    headers: tuple[LatexTableCell, ...],
    rows: tuple[tuple[LatexTableCell, ...], ...],
    output_file: Path,
) -> None:
    align = "l" * len(headers)
    lines = [
        BACKSLASH + "begin{table}[h]",
        BACKSLASH + "centering",
        BACKSLASH + "label{tab:" + table_id + "}",
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


FigureIdentifier = Annotated[str, Field(min_length=1)]


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


LatexMacroName = NewType("LatexMacroName", str)
LatexMacroValue = NewType("LatexMacroValue", str)


@dataclass(frozen=True)
class ArtifactStatusRecord:
    artifact: ArtifactName
    status: ArtifactVerificationStatus


def synthesize_latex_macros(
    macros: tuple[tuple[LatexMacroName, LatexMacroValue], ...], output_file: Path
) -> None:
    lines = [
        BACKSLASH + "newcommand{" + BACKSLASH + name + "}{" + value + "}" for name, value in macros
    ]
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(chr(10).join(lines) + chr(10), encoding="utf-8")


def generate_project_summary(
    project: ArtifactName,
    verdict: ScientificOutcome,
    prospective_fnr: MetricRate,
    certification_rate: MetricRate,
    output_file: Path,
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "project": project,
        "verdict": verdict.value,
        "prospective_fnr": prospective_fnr,
        "certification_rate": certification_rate,
    }
    output_file.write_text(json.dumps(payload, indent=2) + chr(10), encoding="utf-8")


def package_artifact_status_index(
    status_records: list[ArtifactStatusRecord], output_file: Path
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(record) for record in status_records]
    output_file.write_text(json.dumps(payload, indent=2) + chr(10), encoding="utf-8")


def _verification_status(artifact_file: Path) -> ArtifactVerificationStatus:
    if artifact_file.is_file():
        return ArtifactVerificationStatus.VERIFIED
    return ArtifactVerificationStatus.MISSING


def export_verified_project_evidence(
    prospective: WorkflowResultRecord,
    overall_outcome: ScientificOutcome,
    results_directory: Path,
) -> None:
    fnr = prospective.mean_false_negative_rate
    certification_rate = prospective.mean_certification_rate
    degradation = prospective.clean_fnr_degradation_percentage_points
    if fnr is None or certification_rate is None or degradation is None:
        raise ValueError(
            "export requires a prospective evaluation result with false-negative rate, "
            "certification rate, and clean-FNR degradation"
        )

    table_file = results_directory / "tables" / "table_1_main.tex"
    generate_latex_table(
        table_id="main_results",
        headers=tuple(
            LatexTableCell(header)
            for header in (
                "Method",
                "Prospective FNR",
                "Certification Rate",
                "Clean FNR Degradation",
            )
        ),
        rows=(
            tuple(
                LatexTableCell(cell)
                for cell in (
                    "FedACT (Ours)",
                    f"{fnr:.2f}",
                    f"{certification_rate:.2f}",
                    f"{degradation:.1f}%",
                )
            ),
        ),
        output_file=table_file,
    )
    generate_prospective_metrics_figure(
        "fig_1_prospective",
        fnr,
        certification_rate,
        results_directory / "figures" / "fig_1.tex",
    )
    synthesize_latex_macros(
        (
            (LatexMacroName("fedactFNR"), LatexMacroValue(f"{fnr:.2f}")),
            (LatexMacroName("fedactCertRate"), LatexMacroValue(f"{certification_rate:.2f}")),
            (
                LatexMacroName("fedactCleanDegradation"),
                LatexMacroValue(f"{degradation:.1f}%"),
            ),
        ),
        results_directory / "latex" / "macros.tex",
    )
    summary_file = results_directory / "project_summary.json"
    generate_project_summary(
        project="FedACT",
        verdict=overall_outcome,
        prospective_fnr=fnr,
        certification_rate=certification_rate,
        output_file=summary_file,
    )
    package_artifact_status_index(
        [
            ArtifactStatusRecord(
                artifact="table_1_main.tex", status=_verification_status(table_file)
            ),
            ArtifactStatusRecord(
                artifact="project_summary.json", status=_verification_status(summary_file)
            ),
        ],
        results_directory / "evidence_index.json",
    )
