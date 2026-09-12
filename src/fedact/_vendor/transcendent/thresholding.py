from __future__ import annotations

from typing import cast

import numpy as np
import sklearn.metrics as sklearn_metrics
from numpy.typing import NDArray
from dataclasses import dataclass


@dataclass(frozen=True)
class ClassThresholds:
    malicious: float
    benign: float


def apply_threshold(
    binary_thresholds: dict[str, ClassThresholds],  # TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    test_scores: dict[str, list[float]],  # TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    y_test: NDArray[np.int_],
) -> NDArray[np.bool_]:
    assert set(binary_thresholds.keys()) in [{"cred"}, {"conf"}, {"cred", "conf"}]

    for key in binary_thresholds:
        assert key in test_scores

    def get_class_threshold(criteria: str, k: int) -> float:
        threshold = binary_thresholds[criteria]
        return threshold.malicious if k == 1 else threshold.benign

    keep_mask: list[bool] = []
    for i, y_prediction in enumerate(y_test):
        cred_threshold, conf_threshold = 0.0, 0.0
        current_cred, current_conf = 0.0, 0.0

        if "cred" in binary_thresholds:
            current_cred = test_scores["cred"][i]
            cred_threshold = get_class_threshold("cred", int(y_prediction))

        if "conf" in binary_thresholds:
            current_conf = test_scores["conf"][i]
            conf_threshold = get_class_threshold("conf", int(y_prediction))

        keep_mask.append((current_cred >= cred_threshold) and (current_conf >= conf_threshold))

    return np.array(keep_mask, dtype=bool)


def get_performance_with_rejection(
    y_true: NDArray[np.int_],
    y_pred: NDArray[np.int_],
    keep_mask: NDArray[np.bool_],
    full: bool = True,
) -> dict[str, float]:  # TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    d: dict[str, float] = {}  # TODO: do not use primitives. Fix by introducing a proper error type or message class and identify and fix why architecture tests didn't catch this

    total_neg = float(len(y_true) - sum(y_true))
    total_pos = float(sum(y_true))

    kept_total_perc = float(sum(keep_mask) / len(keep_mask))
    reject_total_perc = float(sum(~keep_mask) / len(keep_mask))

    kept_neg = float(len(y_true[keep_mask]) - sum(y_true[keep_mask]))
    kept_pos = float(sum(y_true[keep_mask]))

    reject_neg = total_neg - kept_neg
    reject_pos = total_pos - kept_pos

    kept_neg_perc = kept_neg / total_neg
    kept_pos_perc = kept_pos / total_pos

    reject_neg_perc = 1 - kept_neg_perc
    reject_pos_perc = 1 - kept_pos_perc

    d.update(
        {
            "total_neg": total_neg,
            "total_pos": total_pos,
            "kept_total_perc": kept_total_perc,
            "reject_total_perc": reject_total_perc,
            "kept_neg": kept_neg,
            "kept_pos": kept_pos,
            "reject_neg": reject_neg,
            "reject_pos": reject_pos,
            "kept_neg_perc": kept_neg_perc,
            "kept_pos_perc": kept_pos_perc,
            "reject_neg_perc": reject_neg_perc,
            "reject_pos_perc": reject_pos_perc,
        }
    )

    f1_b = sklearn_metrics.f1_score(y_true, y_pred)
    f1_k = sklearn_metrics.f1_score(y_true[keep_mask], y_pred[keep_mask])
    f1_r = sklearn_metrics.f1_score(y_true[~keep_mask], y_pred[~keep_mask])

    d.update({"f1_b": float(f1_b), "f1_k": float(f1_k), "f1_r": float(f1_r)})

    precision_b = sklearn_metrics.precision_score(y_true, y_pred)
    precision_k = sklearn_metrics.precision_score(y_true[keep_mask], y_pred[keep_mask])
    precision_r = sklearn_metrics.precision_score(y_true[~keep_mask], y_pred[~keep_mask])
    d.update(
        {
            "precision_b": float(precision_b),
            "precision_k": float(precision_k),
            "precision_r": float(precision_r),
        }
    )

    recall_b = sklearn_metrics.recall_score(y_true, y_pred)
    recall_k = sklearn_metrics.recall_score(y_true[keep_mask], y_pred[keep_mask])
    recall_r = sklearn_metrics.recall_score(y_true[~keep_mask], y_pred[~keep_mask])
    d.update(
        {"recall_b": float(recall_b), "recall_k": float(recall_k), "recall_r": float(recall_r)}
    )

    if full:
        cf_baseline = cast(NDArray[np.int_], sklearn_metrics.confusion_matrix(y_true, y_pred))
        cf_keep = cast(
            NDArray[np.int_],
            sklearn_metrics.confusion_matrix(y_true[keep_mask], y_pred[keep_mask]),
        )
        cf_reject = cast(
            NDArray[np.int_],
            sklearn_metrics.confusion_matrix(y_true[~keep_mask], y_pred[~keep_mask]),
        )

        if cf_baseline.size != 4 or cf_keep.size != 4 or cf_reject.size != 4:
            return d

        tn_b, fp_b, fn_b, tp_b = (float(value) for value in cf_baseline.ravel())
        tn_k, fp_k, fn_k, tp_k = (float(value) for value in cf_keep.ravel())
        tn_r, fp_r, fn_r, tp_r = (float(value) for value in cf_reject.ravel())

        d.update(
            {
                "tn_b": tn_b,
                "fp_b": fp_b,
                "fn_b": fn_b,
                "tp_b": tp_b,
                "tn_k": tn_k,
                "fp_k": fp_k,
                "fn_k": fn_k,
                "tp_k": tp_k,
                "tn_r": tn_r,
                "fp_r": fp_r,
                "fn_r": fn_r,
                "tp_r": tp_r,
            }
        )

        d["tpr_b"] = tp_b / (tp_b + fn_b)
        d["tpr_k"] = tp_k / (tp_k + fn_k)
        d["tpr_r"] = tp_r / (tp_r + fn_r)

        d["fpr_b"] = fp_b / (fp_b + tn_b)
        d["fpr_k"] = fp_k / (fp_k + tn_k)
        d["fpr_r"] = fp_r / (fp_r + tn_r)

    return d
