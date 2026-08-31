from __future__ import annotations

from fedact.analysis.claims import classify_confirmatory_contrast, evaluate_paired_contrast_evidence
from fedact.analysis.comparisons import PairedContrastInputs
from fedact.config.loading import LoadedConfiguration
from fedact.domain.enums import EffectDirection, EvidenceStatus


def test_insufficient_contrast_never_computes_evidence(
    production_configuration: LoadedConfiguration,
) -> None:
    contrast = PairedContrastInputs(
        paired_differences=(0.1,),
        eligible_cutoff_count=1,
        missing_cutoff_count=0,
        sufficient=False,
    )
    evidence = evaluate_paired_contrast_evidence(
        contrast,
        production_configuration.values.statistics,
        seed=1,
        p_value_for_decision=0.5,
        correction_applied=True,
    )
    assert evidence is None
    result = classify_confirmatory_contrast(
        evidence, production_configuration.values.statistics, material_effect_satisfied=True
    )
    assert result.evidence_status is EvidenceStatus.INSUFFICIENT_EVIDENCE
    assert result.effect_direction is EffectDirection.NEUTRAL


def test_strongly_favorable_paired_effect_is_supported(
    production_configuration: LoadedConfiguration,
) -> None:
    differences = tuple(1.0 + 0.01 * index for index in range(10))
    contrast = PairedContrastInputs(
        paired_differences=differences,
        eligible_cutoff_count=len(differences),
        missing_cutoff_count=0,
        sufficient=True,
    )
    evidence = evaluate_paired_contrast_evidence(
        contrast,
        production_configuration.values.statistics,
        seed=1,
        p_value_for_decision=0.001,
        correction_applied=True,
    )
    assert evidence is not None
    result = classify_confirmatory_contrast(
        evidence, production_configuration.values.statistics, material_effect_satisfied=True
    )
    assert result.effect_direction is EffectDirection.FAVORABLE
    assert result.evidence_status is EvidenceStatus.SUPPORTED


def test_favorable_direction_without_material_effect_is_insufficient(
    production_configuration: LoadedConfiguration,
) -> None:
    differences = tuple(1.0 + 0.01 * index for index in range(10))
    contrast = PairedContrastInputs(
        paired_differences=differences,
        eligible_cutoff_count=len(differences),
        missing_cutoff_count=0,
        sufficient=True,
    )
    evidence = evaluate_paired_contrast_evidence(
        contrast,
        production_configuration.values.statistics,
        seed=1,
        p_value_for_decision=0.001,
        correction_applied=True,
    )
    assert evidence is not None
    result = classify_confirmatory_contrast(
        evidence, production_configuration.values.statistics, material_effect_satisfied=False
    )
    assert result.evidence_status is EvidenceStatus.INSUFFICIENT_EVIDENCE


def test_strongly_contradictory_paired_effect_is_falsified(
    production_configuration: LoadedConfiguration,
) -> None:
    differences = tuple(-1.0 - 0.01 * index for index in range(10))
    contrast = PairedContrastInputs(
        paired_differences=differences,
        eligible_cutoff_count=len(differences),
        missing_cutoff_count=0,
        sufficient=True,
    )
    evidence = evaluate_paired_contrast_evidence(
        contrast,
        production_configuration.values.statistics,
        seed=1,
        p_value_for_decision=0.001,
        correction_applied=True,
    )
    assert evidence is not None
    result = classify_confirmatory_contrast(
        evidence, production_configuration.values.statistics, material_effect_satisfied=True
    )
    assert result.effect_direction is EffectDirection.CONTRADICTORY
    assert result.evidence_status is EvidenceStatus.FALSIFIED


def test_single_test_family_uses_classical_significance_level(
    production_configuration: LoadedConfiguration,
) -> None:
    differences = tuple(1.0 + 0.01 * index for index in range(10))
    contrast = PairedContrastInputs(
        paired_differences=differences,
        eligible_cutoff_count=len(differences),
        missing_cutoff_count=0,
        sufficient=True,
    )
    evidence = evaluate_paired_contrast_evidence(
        contrast,
        production_configuration.values.statistics,
        seed=1,
        p_value_for_decision=0.049,
        correction_applied=False,
    )
    assert evidence is not None
    result = classify_confirmatory_contrast(
        evidence, production_configuration.values.statistics, material_effect_satisfied=True
    )
    assert result.evidence_status is EvidenceStatus.SUPPORTED
