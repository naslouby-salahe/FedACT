from __future__ import annotations

import numpy as np
import pytest

from fedact._vendor.transcendent.scores import (
    compute_p_values_cred_and_conf,
    compute_single_conf_p_value,
    compute_single_cred_p_value,
)
from fedact._vendor.transcendent.thresholding import (
    ClassThresholds,
    apply_threshold,
    get_performance_with_rejection,
)

BINARY_TRAIN_NCMS = [1.0, 2.0, 3.0, 4.0]
BINARY_GROUNDTRUTH = [0, 0, 1, 1]


def test_cred_p_value_counts_same_class_ncms_at_least_as_extreme() -> None:
    assert (
        compute_single_cred_p_value(
            train_ncms=BINARY_TRAIN_NCMS,
            groundtruth_train=BINARY_GROUNDTRUTH,
            single_test_ncm=3.5,
            single_y_test=1,
        )
        == 0.5
    )


def test_cred_p_value_is_one_when_all_same_class_ncms_are_at_least_as_extreme() -> None:
    assert (
        compute_single_cred_p_value(
            train_ncms=BINARY_TRAIN_NCMS,
            groundtruth_train=BINARY_GROUNDTRUTH,
            single_test_ncm=-10.0,
            single_y_test=0,
        )
        == 1.0
    )


def test_conf_p_value_is_the_complement_of_the_opposite_class_credibility() -> None:
    assert (
        compute_single_conf_p_value(
            train_ncms=BINARY_TRAIN_NCMS,
            groundtruth_train=BINARY_GROUNDTRUTH,
            single_test_ncm=2.0,
            single_y_test=1,
        )
        == 0.0
    )
    assert (
        compute_single_conf_p_value(
            train_ncms=BINARY_TRAIN_NCMS,
            groundtruth_train=BINARY_GROUNDTRUTH,
            single_test_ncm=-10.0,
            single_y_test=1,
        )
        == 1.0
    )


def test_p_value_pair_is_computed_per_test_ncm_in_order() -> None:
    p_values = compute_p_values_cred_and_conf(
        train_ncms=BINARY_TRAIN_NCMS,
        groundtruth_train=BINARY_GROUNDTRUTH,
        test_ncms=[3.5, 1.5],
        y_test=[1, 0],
    )
    assert set(p_values) == {"cred", "conf"}
    assert p_values["cred"] == [0.5, 0.5]
    assert len(p_values["conf"]) == 2


def test_p_value_computation_requires_both_classes_in_the_calibration_set() -> None:
    with pytest.raises(AssertionError):
        compute_single_cred_p_value(
            train_ncms=[1.0, 2.0],
            groundtruth_train=[1, 1],
            single_test_ncm=1.0,
            single_y_test=1,
        )


def test_credibility_threshold_keeps_only_scores_at_or_above_the_class_threshold() -> None:
    masks = apply_threshold(
        binary_thresholds={"cred": ClassThresholds(malicious=0.6, benign=0.2)},
        test_scores={"cred": [0.9, 0.1, 0.6, 0.5]},
        y_test=np.array([1, 0, 1, 0]),
    )
    assert masks.tolist() == [True, False, True, True]


def test_confidence_threshold_applies_independently_of_credibility() -> None:
    masks = apply_threshold(
        binary_thresholds={"conf": ClassThresholds(malicious=0.5, benign=0.5)},
        test_scores={"conf": [0.4, 0.5]},
        y_test=np.array([1, 0]),
    )
    assert masks.tolist() == [False, True]


def test_combined_thresholds_require_both_criteria_to_hold() -> None:
    masks = apply_threshold(
        binary_thresholds={
            "cred": ClassThresholds(malicious=0.5, benign=0.5),
            "conf": ClassThresholds(malicious=0.5, benign=0.5),
        },
        test_scores={"cred": [0.9, 0.9], "conf": [0.1, 0.7]},
        y_test=np.array([1, 1]),
    )
    assert masks.tolist() == [False, True]


def test_threshold_rule_rejects_an_unknown_criterion() -> None:
    with pytest.raises(AssertionError):
        apply_threshold(
            binary_thresholds={"marginal": ClassThresholds(malicious=0.5, benign=0.5)},
            test_scores={"marginal": [0.9]},
            y_test=np.array([1]),
        )


def test_performance_with_rejection_reports_kept_and_rejected_rates() -> None:
    performance = get_performance_with_rejection(
        y_true=np.array([1, 1, 0, 0]),
        y_pred=np.array([1, 1, 0, 0]),
        keep_mask=np.array([True, False, True, False]),
    )
    assert performance["total_pos"] == 2.0
    assert performance["total_neg"] == 2.0
    assert performance["kept_total_perc"] == pytest.approx(0.5)
    assert performance["reject_total_perc"] == pytest.approx(0.5)
    assert performance["kept_pos"] == 1.0
    assert performance["reject_pos"] == 1.0
    assert performance["kept_neg"] == 1.0
    assert performance["reject_neg"] == 1.0
    assert performance["tpr_b"] == pytest.approx(1.0)
    assert performance["fpr_b"] == pytest.approx(0.0)
    assert performance["f1_k"] == pytest.approx(1.0)
    assert "precision_r" in performance
    assert "recall_b" in performance


def test_performance_with_rejection_omits_confusion_details_when_not_requested() -> None:
    performance = get_performance_with_rejection(
        y_true=np.array([1, 1, 0, 0]),
        y_pred=np.array([1, 1, 0, 0]),
        keep_mask=np.array([True, False, True, False]),
        full=False,
    )
    assert "tpr_b" not in performance
    assert "kept_pos_perc" in performance
