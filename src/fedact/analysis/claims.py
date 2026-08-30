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
from fedact.domain.enums import ClaimState, EffectDirection
from fedact.domain.types import (
    ConfirmatoryFlag,
    PValue,
    RankBiserialEffectSize,
    SatisfactionFlag,
    SeedValue,
)

_CLASSICAL_SIGNIFICANCE_LEVEL_FOR_SINGLE_TEST = 0.05


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
    claim_state: ClaimState
    effect_direction: EffectDirection
    evidence: ConfirmatoryContrastEvidence | None


def classify_confirmatory_contrast(
    evidence: ConfirmatoryContrastEvidence | None,
    statistics_config: StatisticsConfig,
    material_effect_satisfied: SatisfactionFlag,
) -> ConfirmatoryContrastResult:
    if evidence is None:
        return ConfirmatoryContrastResult(
            claim_state=ClaimState.INSUFFICIENT_EVIDENCE,
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
            claim_state=ClaimState.FALSIFIED, effect_direction=direction, evidence=evidence
        )

    if direction is EffectDirection.FAVORABLE:
        p_threshold = (
            statistics_config.multiplicity.q
            if evidence.correction_applied
            else _CLASSICAL_SIGNIFICANCE_LEVEL_FOR_SINGLE_TEST
        )
        p_criterion_met = evidence.p_value_for_decision < p_threshold
        if p_criterion_met and material_effect_satisfied:
            return ConfirmatoryContrastResult(
                claim_state=ClaimState.SUPPORTED, effect_direction=direction, evidence=evidence
            )

    return ConfirmatoryContrastResult(
        claim_state=ClaimState.INSUFFICIENT_EVIDENCE, effect_direction=direction, evidence=evidence
    )
