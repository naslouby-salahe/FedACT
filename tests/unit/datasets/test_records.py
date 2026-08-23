from __future__ import annotations

from pathlib import Path

import pytest

from fedact.config.loading import LoadedConfiguration, load_production_configuration
from fedact.config.models import FedActConfig
from fedact.datasets.ember2024 import (
    EmberRawRecord,
    choose_control_matching_level,
    ember_client_semantics,
)
from fedact.datasets.lamda import (
    LamdaRawRecord,
    audit_released_label,
    label_derivation_rule,
    lamda_client_semantics,
    operator_eligibility,
)
from fedact.datasets.preprocessing import (
    FeatureValue,
    PreparedSample,
    PreprocessingRuleError,
    prepare_records,
    select_low_variance_features,
)
from fedact.datasets.records import (
    ClientSemanticsAudit,
    ClientSemanticsClass,
    CohortRecord,
    DatasetEligibilityOutcome,
    DatasetEligibilityRole,
    EligibilityStatus,
    ExclusionReason,
    FeasibilityCondition,
    LabelDerivationRuleError,
    SampleIdentifier,
    SchemaChronologyManifest,
    SchemaManifestField,
    derive_binary_label,
)
from fedact.domain.enums import DatasetSelector
from fedact.domain.records import DatasetIdentity, SplitCutoffIdentity

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="module")
def config() -> FedActConfig:
    loaded: LoadedConfiguration = load_production_configuration(
        REPOSITORY_ROOT / "configs" / "fedact.yaml"
    )
    return loaded.values


def sample(
    sid: str,
    month: int,
    label: bool | None,
    features: tuple[float, ...] = (1.0,),
) -> PreparedSample:
    return PreparedSample(
        sample_id=SampleIdentifier(sid),
        month_index=month,
        label=label,
        family="familia",
        features=tuple(FeatureValue(value) for value in features),
    )


def test_schema_manifest_precedes_any_transformation(config: FedActConfig) -> None:
    manifest = SchemaChronologyManifest(
        dataset=DatasetIdentity("lamda-observed"),
        acquisition_checksum="sha256:abc",
        fields=(
            SchemaManifestField(name="hash", observed=True),
            SchemaManifestField(name="label", observed=True),
            SchemaManifestField(name="family", observed=True),
            SchemaManifestField(name="vt_count", observed=True),
            SchemaManifestField(name="year_month", observed=True),
        ),
        observed_row_count=1_000_000,
        observed_feature_dimension=4561,
        chronology_granularity="year_month",
        first_observed_month=0,
        last_observed_month=143,
    )
    assert manifest.observed_row_count == 1_000_000
    assert manifest.observed_feature_dimension == 4561


def test_documented_counts_are_expectations_not_values(config: FedActConfig) -> None:
    manifest = SchemaChronologyManifest(
        dataset=DatasetIdentity("lamda-observed"),
        acquisition_checksum="sha256:abc",
        fields=(SchemaManifestField(name="year_month", observed=False),),
        observed_row_count=17,
        observed_feature_dimension=None,
        chronology_granularity="year_month",
        first_observed_month=0,
        last_observed_month=1,
    )
    assert manifest.fields[0].observed is False
    assert manifest.observed_feature_dimension is None


def test_lamda_label_rule_benign_malicious_and_discard_bands(config: FedActConfig) -> None:
    rule = label_derivation_rule(config.datasets.lamda)
    assert derive_binary_label(rule, 0) is False
    assert derive_binary_label(rule, 4) is True
    assert derive_binary_label(rule, 9001) is True
    for discarded in config.datasets.lamda.labels.discard_detection_counts:
        with pytest.raises(LabelDerivationRuleError):
            derive_binary_label(rule, discarded)


def test_released_label_agreement_is_required(config: FedActConfig) -> None:
    rule = label_derivation_rule(config.datasets.lamda)
    agreeing = LamdaRawRecord(
        sample_hash=SampleIdentifier("a"),
        year_month="2023-06",
        label=True,
        vt_count=30,
        family=None,
    )
    conflicting = LamdaRawRecord(
        sample_hash=SampleIdentifier("b"),
        year_month="2023-06",
        label=False,
        vt_count=30,
        family=None,
    )
    assert audit_released_label(rule, agreeing) is True
    assert audit_released_label(rule, conflicting) is None


def test_missing_derived_label_uses_vt_count_rule(config: FedActConfig) -> None:
    rule = label_derivation_rule(config.datasets.lamda)
    derived = LamdaRawRecord(
        sample_hash=SampleIdentifier("c"),
        year_month="2023-07",
        label=None,
        vt_count=12,
        family=None,
    )
    assert audit_released_label(rule, derived) is True


def test_duplicate_identical_rows_keep_one_canonical_row(config: FedActConfig) -> None:
    outcome = prepare_records(
        DatasetSelector.LAMDA,
        SplitCutoffIdentity("month-000048"),
        (
            sample("dup", 40, True),
            sample("dup", 40, True),
            sample("solo", 41, False),
        ),
    )
    assert len(outcome.retained) == 2
    assert outcome.exclusion_count(ExclusionReason.CONFLICTING_DUPLICATE) == 0


def test_conflicting_duplicates_exclude_all_conflicting_rows(config: FedActConfig) -> None:
    outcome = prepare_records(
        DatasetSelector.LAMDA,
        SplitCutoffIdentity("month-000048"),
        (
            sample("dup", 40, True),
            sample("dup", 40, False),
        ),
    )
    assert outcome.retained == ()
    assert outcome.exclusion_count(ExclusionReason.CONFLICTING_DUPLICATE) == 1


def test_nonfinite_features_are_excluded_and_recorded(config: FedActConfig) -> None:
    outcome = prepare_records(
        DatasetSelector.LAMDA,
        SplitCutoffIdentity("month-000048"),
        (
            sample("bad", 40, True, (float("nan"),)),
            sample("inf", 40, True, (float("inf"),)),
            sample("good", 40, True, (0.5,)),
        ),
    )
    assert [record.sample_id for record in outcome.retained] == [SampleIdentifier("good")]
    assert outcome.exclusion_count(ExclusionReason.NONFINITE_FEATURE) == 2


def test_missing_identity_or_chronology_excluded_from_chronological_science(
    config: FedActConfig,
) -> None:
    outcome = prepare_records(
        DatasetSelector.LAMDA,
        SplitCutoffIdentity("month-000048"),
        (
            sample("", 40, True),
            PreparedSample(
                sample_id=SampleIdentifier("nomonth"),
                month_index=-1,
                label=True,
                family=None,
                features=(FeatureValue(1.0),),
            ),
            sample("kept", 41, False),
        ),
    )
    assert [record.sample_id for record in outcome.retained] == [SampleIdentifier("kept")]
    assert outcome.exclusion_count(ExclusionReason.MISSING_SAMPLE_IDENTITY) >= 1
    assert outcome.exclusion_count(ExclusionReason.MISSING_CHRONOLOGY) >= 1


def test_no_silent_imputation_features_are_never_filled(config: FedActConfig) -> None:
    population = (sample("a", 1, True, (2.0,)), sample("b", 1, False, (4.0,)))
    low = select_low_variance_features(population, scale_standardization_floor=1e-8)
    assert low == frozenset()


def test_low_variance_features_removed_by_fitted_transform(config: FedActConfig) -> None:
    floor = config.numerical.scale_standardization_floor
    constant = (sample("a", 1, True, (7.0, 0.0)), sample("b", 1, False, (9.0, 0.0)))
    low = select_low_variance_features(constant, scale_standardization_floor=floor)
    assert low == frozenset({1})
    with pytest.raises(PreprocessingRuleError):
        select_low_variance_features((), floor)


def test_support_gate_applies_per_side_without_pooling(config: FedActConfig) -> None:
    minimum = config.identification.minimum_support_per_class
    from fedact.datasets.preprocessing import SupportAssessment, no_adjacent_window_pooling

    passing = SupportAssessment(
        malicious_support_before=minimum,
        malicious_support_after=minimum,
        control_support_before=minimum,
        control_support_after=minimum,
    )
    failing_one_side = SupportAssessment(
        malicious_support_before=minimum - 1,
        malicious_support_after=minimum,
        control_support_before=minimum,
        control_support_after=minimum,
    )
    assert passing.meets_minimum(minimum)
    assert not failing_one_side.meets_minimum(minimum)
    assert no_adjacent_window_pooling(minimum - 1, minimum + 5, minimum) is False
    assert no_adjacent_window_pooling(minimum, minimum, minimum) is True


def test_lamda_is_a_single_corpus_level_client() -> None:
    audit = lamda_client_semantics()
    assert audit.classification is ClientSemanticsClass.CORPUS_LEVEL_CLIENT
    assert audit.supports_natural_federation_claim is False


def test_diagnostic_partition_may_not_claim_natural_federation() -> None:
    with pytest.raises(ValueError):
        _ = ClientSemanticsAudit(
            dataset=DatasetSelector.LAMDA,
            source_field="random_hash",
            classification=ClientSemanticsClass.CORPUS_LEVEL_CLIENT,
            observed_values=("abc123",),
            supports_natural_federation_claim=True,
        )


def test_cohort_record_carries_the_locked_fields() -> None:
    cohort = CohortRecord(
        cohort_id="lamda/familia/2023Q2",
        definition="family=familia",
        availability_timestamp="2023-06",
        dataset_id=DatasetIdentity("lamda"),
        client_id="corpus",
        support_count=250,
        window_start=39,
        window_end=42,
        eligibility_status=EligibilityStatus.ELIGIBLE,
    )
    assert cohort.eligibility_status is EligibilityStatus.ELIGIBLE


def test_feasibility_conditions_narrow_role_instead_of_inventing_semantics() -> None:
    full = DatasetEligibilityOutcome(
        dataset=DatasetSelector.LAMDA,
        satisfied_conditions=frozenset(FeasibilityCondition),
        failed_conditions=frozenset(),
    )
    no_binaries = DatasetEligibilityOutcome(
        dataset=DatasetSelector.LAMDA,
        satisfied_conditions=frozenset(FeasibilityCondition)
        - {FeasibilityCondition.OPERATOR_ARTIFACTS_AVAILABLE},
        failed_conditions=frozenset({FeasibilityCondition.OPERATOR_ARTIFACTS_AVAILABLE}),
    )
    broken_chronology = DatasetEligibilityOutcome(
        dataset=DatasetSelector.LAMDA,
        satisfied_conditions=frozenset(),
        failed_conditions=frozenset({FeasibilityCondition.CHRONOLOGY_VALID}),
    )
    assert full.role is DatasetEligibilityRole.PRIMARY_EVIDENCE
    assert no_binaries.role is DatasetEligibilityRole.SECONDARY_EVIDENCE
    assert broken_chronology.role is DatasetEligibilityRole.UNUSABLE


def test_operator_ineligibility_follows_raw_artifact_presence() -> None:
    assert operator_eligibility(True) is True
    assert operator_eligibility(False) is False


def test_ember_weekly_vs_monthly_control_level_is_deterministic(config: FedActConfig) -> None:
    minimum = config.identification.minimum_support_per_class
    weekly_ok = choose_control_matching_level(
        weekly_support_per_side=minimum,
        minimum_support_per_class=minimum,
        monthly_support_per_side=minimum,
    )
    monthly_only = choose_control_matching_level(
        weekly_support_per_side=minimum - 1,
        minimum_support_per_class=minimum,
        monthly_support_per_side=minimum,
    )
    neither = choose_control_matching_level(
        weekly_support_per_side=minimum - 1,
        minimum_support_per_class=minimum,
        monthly_support_per_side=minimum - 1,
    )
    assert weekly_ok is not None and weekly_ok.weekly is True
    assert monthly_only is not None and monthly_only.weekly is False
    assert neither is None


def test_ember_conservative_timestamp_uses_collection_week_start(config: FedActConfig) -> None:
    from fedact.datasets.ember2024 import conservative_timestamp_month

    assert conservative_timestamp_month("2023-W39") == "2023-W39"
    record = EmberRawRecord(
        sample_hash=SampleIdentifier("x"),
        format_client="win32_pe",
        collection_week="2023-W39",
        family=None,
    )
    assert record.family is None


def test_win32_win64_substrate_is_diagnostic_only() -> None:
    audit = ember_client_semantics(("win32_pe", "win64_pe"))
    assert audit.classification is ClientSemanticsClass.DIAGNOSTIC_PARTITION
    assert audit.supports_natural_federation_claim is False


def test_missing_family_keeps_detection_but_blocks_family_cohort(config: FedActConfig) -> None:
    outcome = prepare_records(
        DatasetSelector.EMBER2024,
        SplitCutoffIdentity("month-000006"),
        (
            PreparedSample(
                sample_id=SampleIdentifier("nofamily"),
                month_index=6,
                label=True,
                family=None,
                features=(FeatureValue(1.0),),
            ),
        ),
    )
    assert len(outcome.retained) == 1
    assert outcome.retained[0].family is None
