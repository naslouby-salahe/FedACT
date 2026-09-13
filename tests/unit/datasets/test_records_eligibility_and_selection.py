from __future__ import annotations

import pytest

from fedact.data.records import (
    DatasetEligibilityOutcome,
    DatasetEligibilityRole,
    HorizonAvailability,
    PreparedSample,
    PreprocessingRuleError,
    SupportAuditResult,
    is_horizon_confirmatory,
    select_low_variance_features,
)
from fedact.domain.types import (
    DatasetSelector,
    FeasibilityCondition,
    FeatureValue,
    SampleIdentifier,
)

OUT_OF_BAND_VT_COUNT = 99
SCALE_STANDARDIZATION_FLOOR = 1.0e-8


def _support(malicious_count: int, control_count: int) -> SupportAuditResult:
    return SupportAuditResult(
        malicious_count=malicious_count,
        control_count=control_count,
        control_strata_count=1,
        operator_eligible_count=1,
    )


def test_support_audits_overlap_only_when_both_sides_have_malicious_samples() -> None:
    assert _support(1, 1).has_temporal_overlap_with(_support(1, 0)) is True
    assert _support(0, 1).has_temporal_overlap_with(_support(1, 1)) is False
    assert _support(1, 1).has_temporal_overlap_with(_support(0, 0)) is False


def test_horizon_is_confirmatory_only_when_observable() -> None:
    assert is_horizon_confirmatory(HorizonAvailability.OBSERVABLE) is True
    assert is_horizon_confirmatory(HorizonAvailability.MISSING_SOURCE_DATA) is False


def test_low_variance_selection_requires_a_training_population() -> None:
    with pytest.raises(PreprocessingRuleError, match="requires a training population"):
        select_low_variance_features((), SCALE_STANDARDIZATION_FLOOR)


def test_low_variance_selection_requires_rectangular_feature_vectors() -> None:
    ragged = (
        PreparedSample(
            sample_id=SampleIdentifier("a"),
            month_index=0,
            label=True,
            family="berbew",
            features=(FeatureValue(1.0), FeatureValue(2.0)),
        ),
        PreparedSample(
            sample_id=SampleIdentifier("b"),
            month_index=0,
            label=True,
            family="berbew",
            features=(FeatureValue(1.0),),
        ),
    )
    with pytest.raises(PreprocessingRuleError, match="ragged feature vectors"):
        select_low_variance_features(ragged, SCALE_STANDARDIZATION_FLOOR)


def test_low_variance_selection_returns_feature_indices() -> None:
    population = tuple(
        PreparedSample(
            sample_id=SampleIdentifier(f"sample-{index}"),
            month_index=0,
            label=True,
            family="berbew",
            features=(FeatureValue(float(index)), FeatureValue(5.0)),
        )
        for index in range(4)
    )
    low_variance = select_low_variance_features(population, SCALE_STANDARDIZATION_FLOOR)
    assert all(isinstance(index, int) for index in low_variance)


def test_eligibility_role_is_primary_when_nothing_failed() -> None:
    outcome = DatasetEligibilityOutcome(
        dataset=DatasetSelector.LAMDA,
        satisfied_conditions=frozenset(FeasibilityCondition),
        failed_conditions=frozenset(),
    )
    assert outcome.role is DatasetEligibilityRole.PRIMARY_EVIDENCE


def test_eligibility_role_is_unusable_when_chronology_failed() -> None:
    outcome = DatasetEligibilityOutcome(
        dataset=DatasetSelector.LAMDA,
        satisfied_conditions=frozenset(FeasibilityCondition)
        - {FeasibilityCondition.CHRONOLOGY_VALID},
        failed_conditions=frozenset({FeasibilityCondition.CHRONOLOGY_VALID}),
    )
    assert outcome.role is DatasetEligibilityRole.UNUSABLE


def test_eligibility_role_is_secondary_for_operator_coverage_gaps_only() -> None:
    failed = frozenset(
        {
            FeasibilityCondition.OPERATOR_ARTIFACTS_AVAILABLE,
            FeasibilityCondition.COHORTS_CUTOFF_SAFE,
        }
    )
    outcome = DatasetEligibilityOutcome(
        dataset=DatasetSelector.LAMDA,
        satisfied_conditions=frozenset(FeasibilityCondition) - failed,
        failed_conditions=failed,
    )
    assert outcome.role is DatasetEligibilityRole.SECONDARY_EVIDENCE


def test_eligibility_role_is_diagnostic_for_other_gaps() -> None:
    failed = frozenset({FeasibilityCondition.MALICIOUS_HISTORY_SUFFICIENT})
    outcome = DatasetEligibilityOutcome(
        dataset=DatasetSelector.LAMDA,
        satisfied_conditions=frozenset(FeasibilityCondition) - failed,
        failed_conditions=failed,
    )
    assert outcome.role is DatasetEligibilityRole.DIAGNOSTIC_ONLY
