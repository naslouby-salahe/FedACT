from __future__ import annotations

import numpy as np

from fedact.data.lamda import LamdaRawRecord, label_derivation_rule
from fedact.data.splits import calendar_month
from fedact.domain.types import AbstentionReason, SampleIdentifier
from fedact.experiments.identification import (
    cohort_has_sufficient_malicious_support,
    dominant_malicious_family_cohort,
    fit_lamda_client_constraint,
    fit_lamda_client_constraint_no_controls,
)
from fedact.workflow import Application

MALICIOUS_VT_COUNT = 8
BENIGN_VT_COUNT = 0
DISCARDED_VT_COUNT = 2
BEFORE_WINDOW_MONTH = "2013-01"
AFTER_WINDOW_MONTH = "2013-04"
ENDPOINT_MONTH = calendar_month(6)
TRANSITION_INTERVAL_MONTHS = 3
FEATURE_DIMENSION = 3


def _malicious(sample_hash: str, year_month: str, family: str = "berbew") -> LamdaRawRecord:
    return LamdaRawRecord(
        sample_hash=SampleIdentifier(sample_hash),
        year_month=year_month,
        label=True,
        vt_count=MALICIOUS_VT_COUNT,
        family=family,
    )


def _benign(sample_hash: str, year_month: str, family: str = "berbew") -> LamdaRawRecord:
    return LamdaRawRecord(
        sample_hash=SampleIdentifier(sample_hash),
        year_month=year_month,
        label=False,
        vt_count=BENIGN_VT_COUNT,
        family=family,
    )


def _discarded(sample_hash: str, year_month: str) -> LamdaRawRecord:
    return LamdaRawRecord(
        sample_hash=SampleIdentifier(sample_hash),
        year_month=year_month,
        label=None,
        vt_count=DISCARDED_VT_COUNT,
        family="berbew",
    )


def _dense_cohort(
    samples_per_window: int,
) -> tuple[tuple[LamdaRawRecord, ...], np.ndarray]:
    records: list[LamdaRawRecord] = []
    features: list[list[float]] = []
    for window_offset, year_month in ((0.0, BEFORE_WINDOW_MONTH), (1.0, AFTER_WINDOW_MONTH)):
        for index in range(samples_per_window):
            records.append(_malicious(f"{year_month}-{index}", year_month))
            features.append(
                [
                    window_offset + float(index % 11) / 10.0,
                    window_offset + float(index % 7) / 10.0,
                    window_offset,
                ]
            )
    return tuple(records), np.array(features, dtype=np.float64)


def test_cohort_support_requires_enough_malicious_samples_in_both_windows(
    application: Application,
) -> None:
    rule = label_derivation_rule(application.configuration.values.datasets.lamda)
    records = (
        _malicious("before-1", BEFORE_WINDOW_MONTH),
        _malicious("before-2", BEFORE_WINDOW_MONTH),
        _malicious("after-1", AFTER_WINDOW_MONTH),
        _malicious("after-2", AFTER_WINDOW_MONTH),
    )
    assert (
        cohort_has_sufficient_malicious_support(
            records, rule, ENDPOINT_MONTH, TRANSITION_INTERVAL_MONTHS, 2
        )
        is True
    )
    assert (
        cohort_has_sufficient_malicious_support(
            records, rule, ENDPOINT_MONTH, TRANSITION_INTERVAL_MONTHS, 3
        )
        is False
    )


def test_cohort_support_ignores_benign_and_discarded_records(application: Application) -> None:
    rule = label_derivation_rule(application.configuration.values.datasets.lamda)
    records = (
        _benign("benign-before", BEFORE_WINDOW_MONTH),
        _benign("benign-after", AFTER_WINDOW_MONTH),
        _discarded("discarded-before", BEFORE_WINDOW_MONTH),
        _discarded("discarded-after", AFTER_WINDOW_MONTH),
    )
    assert (
        cohort_has_sufficient_malicious_support(
            records, rule, ENDPOINT_MONTH, TRANSITION_INTERVAL_MONTHS, 1
        )
        is False
    )


def test_dominant_cohort_is_the_family_with_the_most_malicious_samples(
    application: Application,
) -> None:
    rule = label_derivation_rule(application.configuration.values.datasets.lamda)
    records = (
        _malicious("a-1", BEFORE_WINDOW_MONTH, family="berbew"),
        _malicious("a-2", BEFORE_WINDOW_MONTH, family="berbew"),
        _malicious("a-3", AFTER_WINDOW_MONTH, family="berbew"),
        _malicious("b-1", BEFORE_WINDOW_MONTH, family="drixed"),
        _benign("benign-1", BEFORE_WINDOW_MONTH, family="drixed"),
        _benign("benign-2", BEFORE_WINDOW_MONTH, family="drixed"),
    )
    assert dominant_malicious_family_cohort(records, rule) == "berbew"


def test_dominant_cohort_is_absent_without_malicious_samples(application: Application) -> None:
    rule = label_derivation_rule(application.configuration.values.datasets.lamda)
    records = (
        _benign("benign-1", BEFORE_WINDOW_MONTH),
        _discarded("discarded-1", AFTER_WINDOW_MONTH),
    )
    assert dominant_malicious_family_cohort(records, rule) is None
    assert dominant_malicious_family_cohort((), rule) is None


def test_no_controls_fit_abstains_when_malicious_support_is_thin(
    application: Application,
) -> None:
    rule = label_derivation_rule(application.configuration.values.datasets.lamda)
    records, features = _dense_cohort(2)
    result = fit_lamda_client_constraint_no_controls(
        application, records, features, rule, ENDPOINT_MONTH, ()
    )
    assert result is AbstentionReason.ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT


def test_no_controls_fit_abstains_without_private_allowance_history(
    application: Application,
) -> None:
    rule = label_derivation_rule(application.configuration.values.datasets.lamda)
    records, features = _dense_cohort(250)
    result = fit_lamda_client_constraint_no_controls(
        application, records, features, rule, ENDPOINT_MONTH, ()
    )
    assert result is AbstentionReason.ABSTAIN_INSUFFICIENT_PRIVATE_ALLOWANCE_HISTORY


def test_top_level_fit_abstains_when_malicious_support_is_thin(application: Application) -> None:
    rule = label_derivation_rule(application.configuration.values.datasets.lamda)
    records, features = _dense_cohort(2)
    result = fit_lamda_client_constraint(
        application,
        records,
        features,
        records,
        features,
        rule,
        ENDPOINT_MONTH,
        (calendar_month(0), calendar_month(1)),
        (),
    )
    assert result is AbstentionReason.ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT


def test_top_level_fit_abstains_without_a_usable_control_transition(
    application: Application,
) -> None:
    rule = label_derivation_rule(application.configuration.values.datasets.lamda)
    records, features = _dense_cohort(250)
    result = fit_lamda_client_constraint(
        application,
        records,
        features,
        records,
        features,
        rule,
        ENDPOINT_MONTH,
        (),
        (),
    )
    assert result is AbstentionReason.ABSTAIN_NO_USABLE_CONTROL
