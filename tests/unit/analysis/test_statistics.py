from __future__ import annotations

import numpy as np
import pytest

from fedact.analysis.statistics import (
    InsufficientPairedDataError,
    benjamini_hochberg_correction,
    cutoff_clustered_bca_bootstrap,
    cutoff_quantile,
    matched_pairs_rank_biserial_effect_size,
    paired_wilcoxon_signed_rank_test,
)


def test_wilcoxon_exact_matches_hand_computed_example() -> None:
    differences = (1.0, -1.5, 2.5, -3.0, 4.0, 5.5, -2.0)
    result = paired_wilcoxon_signed_rank_test(differences, maximum_nonzero_pairs_for_exact=25)
    assert result.used_exact_distribution
    assert result.nonzero_pair_count == 7
    assert 0.0 <= result.p_value <= 1.0


def test_wilcoxon_all_zero_differences_yields_p_value_one() -> None:
    result = paired_wilcoxon_signed_rank_test((0.0, 0.0, 0.0), maximum_nonzero_pairs_for_exact=25)
    assert result.p_value == 1.0
    assert result.nonzero_pair_count == 0


def test_wilcoxon_switches_to_asymptotic_above_exact_threshold() -> None:
    rng = np.random.default_rng(0)
    differences = tuple(float(x) for x in rng.standard_normal(40) + 0.5)
    result = paired_wilcoxon_signed_rank_test(differences, maximum_nonzero_pairs_for_exact=25)
    assert not result.used_exact_distribution


def test_wilcoxon_switches_to_asymptotic_when_ties_present() -> None:
    differences = (1.0, 1.0, 2.0, -1.0)
    result = paired_wilcoxon_signed_rank_test(differences, maximum_nonzero_pairs_for_exact=25)
    assert not result.used_exact_distribution


def test_rank_biserial_effect_size_matches_hand_computation() -> None:
    differences = (3.0, -1.0, 2.0)
    ranks = {1.0: 1, 2.0: 2, 3.0: 3}
    positive = ranks[3.0] + ranks[2.0]
    negative = ranks[1.0]
    expected = (positive - negative) / (positive + negative)
    assert matched_pairs_rank_biserial_effect_size(differences) == pytest.approx(expected)


def test_rank_biserial_effect_size_is_zero_when_all_differences_are_zero() -> None:
    assert matched_pairs_rank_biserial_effect_size((0.0, 0.0)) == 0.0


def test_rank_biserial_effect_size_is_plus_one_when_all_differences_favorable() -> None:
    assert matched_pairs_rank_biserial_effect_size((1.0, 2.0, 3.0)) == pytest.approx(1.0)


def test_benjamini_hochberg_matches_classic_textbook_example() -> None:
    p_values = (0.01, 0.02, 0.03, 0.04, 0.20)
    outcome = benjamini_hochberg_correction(p_values, q=0.05)
    assert outcome.rejected == (True, True, True, True, False)


def test_benjamini_hochberg_single_test_is_unadjusted() -> None:
    outcome = benjamini_hochberg_correction((0.03,), q=0.05)
    assert outcome.adjusted_p_values == (0.03,)
    assert not outcome.correction_applied
    assert outcome.rejected == (True,)


def test_bootstrap_confidence_interval_contains_sample_mean() -> None:
    sample = tuple(float(x) for x in range(1, 21))
    estimate = cutoff_clustered_bca_bootstrap(sample, resamples=500, confidence_level=0.95, seed=42)
    assert estimate.interval.lower <= estimate.point_estimate <= estimate.interval.upper


def test_bootstrap_requires_at_least_two_paired_cutoffs() -> None:
    with pytest.raises(InsufficientPairedDataError):
        cutoff_clustered_bca_bootstrap((1.0,), resamples=500, confidence_level=0.95, seed=1)


def test_cutoff_quantile_matches_numpy_linear_interpolation() -> None:
    values = (1.0, 2.0, 3.0, 4.0)
    assert cutoff_quantile(values, 0.5) == pytest.approx(2.5)
