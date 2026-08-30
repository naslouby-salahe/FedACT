from __future__ import annotations

from pathlib import Path

from fedact.artifacts.results import WorkflowResultRecord
from fedact.domain.enums import EvidenceVerificationStatus, ScientificOutcome
from fedact.reporting.evidence import EvidenceArtifactRecord, package_evidence_index
from fedact.reporting.figures import generate_prospective_metrics_figure
from fedact.reporting.latex import (
    LatexMacro,
    LatexMacroName,
    LatexMacroValue,
    synthesize_latex_macros,
)
from fedact.reporting.summary import ProjectSummaryPayload, generate_project_summary
from fedact.reporting.tables import LatexTableCell, generate_latex_table


def _verification_status(artifact_file: Path) -> EvidenceVerificationStatus:
    if artifact_file.is_file():
        return EvidenceVerificationStatus.VERIFIED
    return EvidenceVerificationStatus.MISSING


def generate_project_report(
    prospective: WorkflowResultRecord,
    overall_outcome: ScientificOutcome,
    results_directory: Path,
) -> None:
    fnr = prospective.mean_false_negative_rate
    certification_rate = prospective.mean_certification_rate
    degradation = prospective.clean_fnr_degradation_percentage_points
    if fnr is None or certification_rate is None or degradation is None:
        raise ValueError(
            "generate_project_report requires a prospective evaluation result "
            "with false-negative rate, certification rate, and clean-FNR degradation"
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
        tuple(
            LatexMacro(name=LatexMacroName(name), value=LatexMacroValue(value))
            for name, value in (
                ("fedactFNR", f"{fnr:.2f}"),
                ("fedactCertRate", f"{certification_rate:.2f}"),
                ("fedactCleanDegradation", f"{degradation:.1f}%"),
            )
        ),
        results_directory / "latex" / "macros.tex",
    )
    summary_file = results_directory / "project_summary.json"
    generate_project_summary(
        ProjectSummaryPayload(
            project="FedACT",
            verdict=overall_outcome,
            prospective_fnr=fnr,
            certification_rate=certification_rate,
        ),
        summary_file,
    )
    package_evidence_index(
        [
            EvidenceArtifactRecord(
                artifact="table_1_main.tex", status=_verification_status(table_file)
            ),
            EvidenceArtifactRecord(
                artifact="project_summary.json", status=_verification_status(summary_file)
            ),
        ],
        results_directory / "evidence_index.json",
    )
