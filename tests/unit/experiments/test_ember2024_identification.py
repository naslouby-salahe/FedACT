from __future__ import annotations

import numpy as np

from fedact.data.ember2024 import EmberRawRecord
from fedact.data.splits import calendar_month
from fedact.domain.types import AbstentionReason, SampleIdentifier
from fedact.experiments.ember2024_identification import fit_ember2024_client_constraint
from fedact.workflow import Application


def _tiny_records_and_features() -> tuple[tuple[EmberRawRecord, ...], np.ndarray]:
    records: list[EmberRawRecord] = []
    features: list[list[float]] = []
    for year_month, label in (("2023-09", True), ("2023-10", True)):
        for sample_index in range(5):
            records.append(
                EmberRawRecord(
                    sample_hash=SampleIdentifier(f"{year_month}-{sample_index}"),
                    year_month=year_month,
                    label=label,
                    family="berbew",
                )
            )
            features.append([float(sample_index), 0.0])
    return tuple(records), np.array(features, dtype=np.float64)


def test_fit_ember2024_client_constraint_abstains_on_insufficient_malicious_support(
    application: Application,
) -> None:
    records, features = _tiny_records_and_features()
    endpoint = calendar_month(6)
    result = fit_ember2024_client_constraint(
        application,
        records,
        features,
        records,
        features,
        endpoint,
        (calendar_month(0), calendar_month(1)),
        (),
    )
    assert result is AbstentionReason.ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT
