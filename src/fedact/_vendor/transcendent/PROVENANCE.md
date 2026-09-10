# Vendored: transcendent-release

Source: https://github.com/s2labres/transcendent-release
Commit: dc62d5019eb345cc4bc4b44c83749611e3b7ba59 (2023-12-08 12:43:07 +0000)
License: BSD-3-Clause (Royal Holloway, University of London & King's College London) — see LICENSE

## Checksums of original unmodified files this vendoring was derived from

```
2084666e2016c77883f7ca4d6db9d841c7f36d5af973c249140f55d32143c3ac  transcend/scores.py
59c75a076ba7903106017e196ba88356f2f9d4e6b1e178742ca698569e6e73e1  transcend/thresholding.py
c4f937695ec3b3ddaa474e4680eb91bbea2d84a40fc993dbc92f3f13d4d3abbb  transcend/utils.py
a20486113c5fbc438db5a8da0ba8afbd0fe5967aa38130f587ec44c4ebf1011f  LICENSE
```

## Scope

`scores.py`: kept `compute_single_cred_p_value`, `compute_single_conf_p_value`,
`compute_p_values_cred_and_conf`. These are classifier-agnostic conformal
p-value computations operating on precomputed non-conformity measures (NCMs).
Omitted `get_svm_ncms`, `get_single_svm_ncm`, `get_svm_probs`: these compute
NCMs specifically from `sklearn.svm.SVC.decision_function`/`predict_proba`.
FedACT uses a torch `DetectorHead` with a probability score output, not an
SVM, so the NCM is computed on the FedACT side instead
(`fedact.experiments.generalization`).

`thresholding.py`: kept `apply_threshold` and `get_performance_with_rejection`.
Both apply a given threshold and report resulting metrics regardless of how
the threshold was selected. Omitted every threshold-search function
(`find_quartile_thresholds`, `find_random_search_thresholds*`,
`full_search_with_constraints*`, `all_threshold_tuples`, `random_threshold`,
`sort_by_predicted_label`, `report_results`, `format_opts`) and
`test_with_rejection` (a thin composition of the two kept functions, not
otherwise needed). FedACT selects credibility/confidence thresholds using its
own nested pre-cutoff calibration discipline
(`fedact.certification.calibration.select_best_calibration_candidate`)
instead of Transcendent's own threshold search.

`calibration.py`: omitted entirely. It trains its own per-fold `sklearn.svm.SVC`
classifiers via `StratifiedKFold`/`LeaveOneOut` to derive thresholds — this is
exactly the mechanism FedACT replaces with its own nested pre-cutoff
calibration.

`data.py`, `utils.py`: omitted entirely (pickle/argparse/logging boilerplate
for the paper's own standalone scripts; not needed once `thresholding.py` is
trimmed to the two threshold-application functions).

The upstream `tesseract-ml-release` package (imported only by
`transcendent-release`'s own top-level driver scripts, never by the
`transcend/` core module) was not vendored: FedACT already has its own
chronology-safe time-aware splitting (`fedact.data.splits`).

Per CLAUDE.md's blanket "no comments or docstrings in Python source" rule
(no exception carved out for vendored code), the kept functions below have
had their original docstrings and comments removed; their logic is otherwise
unmodified. This file and LICENSE carry the required attribution instead.
