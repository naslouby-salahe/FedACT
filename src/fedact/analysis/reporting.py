from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import NewType

import pandas as pd
from matplotlib import pyplot as plt

from fedact.artifacts import WorkflowResultRecord
from fedact.domain.types import (
    ArtifactName,
    ArtifactVerificationStatus,
    EpochCount,
    FigureIdentifier,
    MetricRate,
    ScientificOutcome,
    TableIdentifier,
)

LatexTableCell = NewType("LatexTableCell", str) #TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this


def generate_latex_table(
    table_id: TableIdentifier,
    headers: tuple[LatexTableCell, ...],
    rows: tuple[tuple[LatexTableCell, ...], ...],
    output_file: Path,
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    table = pd.DataFrame(rows, columns=headers)
    output_file.write_text(
        table.to_latex(index=False, label=f"tab:{table_id}", position="h"), encoding="utf-8"
    )


def generate_prospective_metrics_figure(
    figure_name: FigureIdentifier,
    mean_false_negative_rate: MetricRate,
    mean_certification_rate: MetricRate,
    rate_significant_figures: EpochCount,
    output_file: Path,
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    labels = ("Prospective FNR", "Certification rate")
    values = (mean_false_negative_rate, mean_certification_rate)
    figure, axis = plt.subplots(figsize=(6.4, 4.0))
    bars = axis.bar(labels, values, color=("#b54708", "#027a48"))
    axis.set_ylim(0.0, 1.0)
    axis.set_ylabel("Rate")
    axis.set_title(figure_name)
    axis.bar_label(
        bars,
        labels=[f"{value:.{rate_significant_figures}f}" for value in values],
        padding=0,
    )
    figure.tight_layout()
    figure.savefig(output_file, dpi=300)
    plt.close(figure)


@dataclass(frozen=True)
class ArtifactStatusRecord:
    artifact: ArtifactName
    status: ArtifactVerificationStatus


def generate_project_summary(
    project: ArtifactName,
    verdict: ScientificOutcome,
    prospective_fnr: MetricRate,
    certification_rate: MetricRate,
    output_file: Path,
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "project": project, #TODO: should be enums not hardcoded strings
        "verdict": verdict, #TODO: should be enums not hardcoded strings
        "prospective_fnr": prospective_fnr, #TODO: should be enums not hardcoded strings
        "certification_rate": certification_rate, #TODO: should be enums not hardcoded strings
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
    rate_significant_figures: EpochCount,
) -> None:
    fnr = prospective.mean_false_negative_rate
    certification_rate = prospective.mean_certification_rate
    degradation = prospective.clean_fnr_degradation_percentage_points
    if fnr is None or certification_rate is None or degradation is None:
        raise ValueError(
            "export requires a prospective evaluation result with false-negative rate, "
            "certification rate, and clean-FNR degradation"
        )

    static_chronological_fnr = prospective.static_chronological_false_negative_rate
    headers = (
        "Method",
        "Prospective FNR",
        "Certification Rate",
        "Clean FNR Degradation",
    )
    rows = [
        (
            "FedACT (Ours)",
            f"{fnr:.{rate_significant_figures}f}",
            f"{certification_rate:.{rate_significant_figures}f}",
            f"{degradation:.{rate_significant_figures}f}%",
        )
    ]
    if static_chronological_fnr is not None:
        rows.append(
            (
                "Static chronological detector (no hardening)",
                f"{static_chronological_fnr:.{rate_significant_figures}f}",
                "n/a",
                "n/a",
            )
        )
    table_file = results_directory / "tables" / "main" / "table_1_main.tex" #TODO: should be enums not hardcoded strings
    generate_latex_table(
        table_id="main_results",
        headers=tuple(LatexTableCell(header) for header in headers),
        rows=tuple(tuple(LatexTableCell(cell) for cell in row) for row in rows),
        output_file=table_file,
    )
    figure_file = results_directory / "figures" / "main" / "fig_1.png" #TODO: should be enums not hardcoded strings
    generate_prospective_metrics_figure(
        "fig_1_prospective",
        fnr,
        certification_rate,
        rate_significant_figures,
        figure_file,
    )
    summary_file = results_directory / "metrics" / "summary" / "project_summary.json" #TODO: should be enums not hardcoded strings
    generate_project_summary(
        project="FedACT",
        verdict=overall_outcome,
        prospective_fnr=fnr,
        certification_rate=certification_rate,
        output_file=summary_file,
    )
    evidence_index_file = (
        results_directory / "reproducibility" / "execution" / "evidence_index.json" #TODO: should be enums not hardcoded strings
    )
    package_artifact_status_index(
        [
            ArtifactStatusRecord(
                artifact="table_1_main.tex", status=_verification_status(table_file)
            ),
            ArtifactStatusRecord(
                artifact="fig_1.png",
                status=_verification_status(figure_file),
            ),
            ArtifactStatusRecord(
                artifact="project_summary.json", status=_verification_status(summary_file)
            ),
        ],
        evidence_index_file,
    )
