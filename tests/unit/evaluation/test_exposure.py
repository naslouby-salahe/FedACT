from __future__ import annotations

from fedact.evaluation.exposure import compute_cumulative_exposure, compute_time_to_catch_up


def test_exposure_calculations() -> None:
    losses = [0.1, 0.2, 0.3]
    assert compute_cumulative_exposure(losses) == 0.6

    b_losses = [0.5, 0.4, 0.3, 0.2]
    h_losses = [0.2, 0.2, 0.2, 0.2]
    ttc = compute_time_to_catch_up(b_losses, h_losses, threshold=0.01)
    assert ttc == 3
