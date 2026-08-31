from __future__ import annotations

from dataclasses import dataclass

from fedact.analysis.comparisons import PairedContrastInputs
from fedact.analysis.statistics import (
    BootstrapEstimate,
    WilcoxonSignedRankResult,
    cutoff_clustered_bca_bootstrap,
    matched_pairs_rank_biserial_effect_size,
    paired_wilcoxon_signed_rank_test,
)
from fedact.config.models import StatisticsConfig
from fedact.domain.enums import EffectDirection, EvidenceStatus
from fedact.domain.records import (
    ConfirmatoryFlag,
    PValue,
    RankBiserialEffectSize,
    SatisfactionFlag,
    SeedValue,
)


@dataclass(frozen=True)
class ConfirmatoryContrastEvidence:
    contrast_inputs: PairedContrastInputs
    bootstrap: BootstrapEstimate
    wilcoxon: WilcoxonSignedRankResult
    effect_size: RankBiserialEffectSize
    p_value_for_decision: PValue
    correction_applied: ConfirmatoryFlag


def evaluate_paired_contrast_evidence(
    contrast_inputs: PairedContrastInputs,
    statistics_config: StatisticsConfig,
    seed: SeedValue,
    p_value_for_decision: PValue,
    correction_applied: ConfirmatoryFlag,
) -> ConfirmatoryContrastEvidence | None:
    if not contrast_inputs.sufficient:
        return None
    bootstrap = cutoff_clustered_bca_bootstrap(
        contrast_inputs.paired_differences,
        resamples=statistics_config.bootstrap.resamples,
        confidence_level=statistics_config.confidence_level,
        seed=seed,
    )
    wilcoxon = paired_wilcoxon_signed_rank_test(
        contrast_inputs.paired_differences,
        maximum_nonzero_pairs_for_exact=statistics_config.wilcoxon.maximum_nonzero_pairs_for_exact,
    )
    effect_size = matched_pairs_rank_biserial_effect_size(contrast_inputs.paired_differences)
    return ConfirmatoryContrastEvidence(
        contrast_inputs=contrast_inputs,
        bootstrap=bootstrap,
        wilcoxon=wilcoxon,
        effect_size=effect_size,
        p_value_for_decision=p_value_for_decision,
        correction_applied=correction_applied,
    )


@dataclass(frozen=True)
class ConfirmatoryContrastResult:
    evidence_status: EvidenceStatus
    effect_direction: EffectDirection
    evidence: ConfirmatoryContrastEvidence | None


def classify_confirmatory_contrast(
    evidence: ConfirmatoryContrastEvidence | None,
    statistics_config: StatisticsConfig,
    material_effect_satisfied: SatisfactionFlag,
) -> ConfirmatoryContrastResult:
    if evidence is None:
        return ConfirmatoryContrastResult(
            evidence_status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
            effect_direction=EffectDirection.NEUTRAL,
            evidence=None,
        )
    if evidence.bootstrap.interval.excludes_zero_favorably():
        direction = EffectDirection.FAVORABLE
    elif evidence.bootstrap.interval.excludes_zero_contrarily():
        direction = EffectDirection.CONTRADICTORY
    else:
        direction = EffectDirection.NEUTRAL

    if direction is EffectDirection.CONTRADICTORY:
        return ConfirmatoryContrastResult(
            evidence_status=EvidenceStatus.FALSIFIED, effect_direction=direction, evidence=evidence
        )

    if direction is EffectDirection.FAVORABLE:
        p_threshold = statistics_config.multiplicity.q
        p_criterion_met = evidence.p_value_for_decision < p_threshold
        if p_criterion_met and material_effect_satisfied:
            return ConfirmatoryContrastResult(
                evidence_status=EvidenceStatus.SUPPORTED,
                effect_direction=direction,
                evidence=evidence,
            )

    return ConfirmatoryContrastResult(
        evidence_status=EvidenceStatus.INSUFFICIENT_EVIDENCE,
        effect_direction=direction,
        evidence=evidence,
    )
