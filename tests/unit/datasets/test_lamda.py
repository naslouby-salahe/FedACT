from __future__ import annotations

from pathlib import Path

import numpy as np

from fedact.data.lamda import (
    LamdaRawRecord,
    control_transition_replicates,
    filter_low_variance_features,
    load_lamda_records,
    sparse_control_transition_replicates,
    standardize_features,
    validate_lamda_dataset,
)
from fedact.data.records import LabelDerivationRule
from fedact.data.splits import calendar_month
from fedact.domain.types import SampleIdentifier, WindowSpanMonths


def test_lamda_dataset_pipeline(tmp_path: Path) -> None:
    ds = load_lamda_records(tmp_path)
    validate_lamda_dataset(ds)
    feats = np.random.randn(10, 20).astype(np.float32)
    filtered = filter_low_variance_features(feats, variance_threshold=1e-4)
    assert filtered.shape[1] <= 20
    standardized = standardize_features(filtered)
    assert standardized.shape == filtered.shape


def _control_records_and_features() -> tuple[tuple[LamdaRawRecord, ...], np.ndarray]:
    rule_benign_count = 0
    records: list[LamdaRawRecord] = []
    features: list[list[float]] = []
    for month_index, year_month in enumerate(("2013-01", "2013-02")):
        for sample_index in range(20):
            records.append(
                LamdaRawRecord(
                    sample_hash=SampleIdentifier(f"m{month_index}-s{sample_index}"),
                    year_month=year_month,
                    label=False,
                    vt_count=rule_benign_count,
                    family=None,
                )
            )
            features.append([float(month_index), float(sample_index)])
    return tuple(records), np.array(features, dtype=np.float64)


def test_sparse_control_transition_replicates_retains_fraction_of_samples() -> None:
    records, features = _control_records_and_features()
    rule = LabelDerivationRule(
        benign_detection_count=0,
        malware_minimum_detection_count=5,
        discard_detection_counts=(),
    )
    endpoint = calendar_month(2)
    interval: WindowSpanMonths = 1
    full = control_transition_replicates(records, features, rule, (endpoint,), interval)
    assert len(full) == 1
    assert full[0].support_before == 20
    assert full[0].support_after == 20

    sparse = sparse_control_transition_replicates(
        records, features, rule, (endpoint,), interval, retention_fraction=0.5
    )
    assert len(sparse) == 1
    assert sparse[0].support_before == 10
    assert sparse[0].support_after == 10
    assert sparse[0].support_before < full[0].support_before

    repeated = sparse_control_transition_replicates(
        records, features, rule, (endpoint,), interval, retention_fraction=0.5
    )
    np.testing.assert_array_equal(sparse[0].displacement, repeated[0].displacement)
