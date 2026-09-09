from __future__ import annotations

from fedact.experiments.validation import run_nested_calibration
from fedact.workflow import Application


def test_nested_calibration_requires_pre_cutoff_pseudo_future_artifacts(
    application: Application,
) -> None:
    candidates = run_nested_calibration(application)
    assert candidates == ()
