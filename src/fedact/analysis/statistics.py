from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import numpy as np
from scipy import stats as scipy_stats

from fedact.domain.records import (
    CutoffCount,
    CutoffDifferenceValue,
    MetricRate,
    PValue,
    RankBiserialEffectSize,
    ResampleCount,
    SeedValue,
    ThresholdValue,
    ZeroExclusionFlag,
)

_BOOTSTRAP_CONFIDENCE_INTERVAL_ATTRIBUTE = "confidence_interval"
_CONFIDENCE_INTERVAL_LOWER_ATTRIBUTE = "low"
_CONFIDENCE_INTERVAL_UPPER_ATTRIBUTE = "high"
_WILCOXON_STATISTIC_ATTRIBUTE = "statistic"
_WILCOXON_P_VALUE_ATTRIBUTE = "pvalue"


class InsufficientPairedDataError(ValueError):
    pass


@dataclass(frozen=True)
class ConfidenceInterval:
    lower: ThresholdValue
    upper: ThresholdValue
    confidence_level: MetricRate

    def excludes_zero_favorably(self) -> ZeroExclusionFlag:
        return self.lower > 0.0

    def excludes_zero_contrarily(self) -> ZeroExclusionFlag:
        return self.upper < 0.0


@dataclass(frozen=True)
class BootstrapEstimate:
    point_estimate: ThresholdValue
    interval: ConfidenceInterval
    resamples: ResampleCount


def cutoff_clustered_bca_bootstrap(
    paired_differences: tuple[CutoffDifferenceValue, ...],
    resamples: ResampleCount,
    confidence_level: MetricRate,
    seed: SeedValue,
) -> BootstrapEstimate:
    if len(paired_differences) < 2:
        raise InsufficientPairedDataError(
            "cutoff-clustered BCa bootstrap requires at least two paired cutoffs"
        )
    sample = np.asarray(paired_differences, dtype=np.float64)
    rng = np.random.default_rng(seed)
    result = scipy_stats.bootstrap(
        (sample,),
        np.mean,
        method="BCa",
        n_resamples=resamples,
        confidence_level=confidence_level,
        rng=rng,
        vectorized=True,
    )
    confidence_interval = cast(
        object, getattr(cast(object, result), _BOOTSTRAP_CONFIDENCE_INTERVAL_ATTRIBUTE)
    )
    lower = cast(float, getattr(confidence_interval, _CONFIDENCE_INTERVAL_LOWER_ATTRIBUTE))
    upper = cast(float, getattr(confidence_interval, _CONFIDENCE_INTERVAL_UPPER_ATTRIBUTE))
    return BootstrapEstimate(
        point_estimate=float(np.mean(sample)),
        interval=ConfidenceInterval(
            lower=float(lower),
            upper=float(upper),
            confidence_level=confidence_level,
        ),
        resamples=resamples,
    )


@dataclass(frozen=True)
class WilcoxonSignedRankResult:
    statistic: float
    p_value: PValue
    used_exact_distribution: bool
    nonzero_pair_count: CutoffCount


def paired_wilcoxon_signed_rank_test(
    paired_differences: tuple[CutoffDifferenceValue, ...],
    maximum_nonzero_pairs_for_exact: CutoffCount,
) -> WilcoxonSignedRankResult:
    differences = np.asarray(paired_differences, dtype=np.float64)
    nonzero = differences[differences != 0.0]
    nonzero_count = int(nonzero.size)
    if nonzero_count == 0:
        return WilcoxonSignedRankResult(
            statistic=0.0,
            p_value=1.0,
            used_exact_distribution=False,
            nonzero_pair_count=0,
        )
    absolute_nonzero = np.abs(nonzero)
    has_ties = np.unique(absolute_nonzero).size != absolute_nonzero.size
    use_exact = nonzero_count <= maximum_nonzero_pairs_for_exact and not has_ties
    result = scipy_stats.wilcoxon(
        differences,
        zero_method="pratt",
        method="exact" if use_exact else "approx",
        correction=not use_exact,
        alternative="two-sided",
    )
    statistic = cast(float, getattr(cast(object, result), _WILCOXON_STATISTIC_ATTRIBUTE))
    p_value = cast(float, getattr(cast(object, result), _WILCOXON_P_VALUE_ATTRIBUTE))
    return WilcoxonSignedRankResult(
        statistic=float(statistic),
        p_value=float(p_value),
        used_exact_distribution=use_exact,
        nonzero_pair_count=nonzero_count,
    )


def matched_pairs_rank_biserial_effect_size(
    paired_differences: tuple[CutoffDifferenceValue, ...],
) -> RankBiserialEffectSize:
    differences = np.asarray(paired_differences, dtype=np.float64)
    ranks = scipy_stats.rankdata(np.abs(differences))
    signed_ranks = np.sign(differences) * ranks
    positive_rank_sum = float(signed_ranks[signed_ranks > 0].sum())
    negative_rank_sum = float(-signed_ranks[signed_ranks < 0].sum())
    total_rank_sum = positive_rank_sum + negative_rank_sum
    if total_rank_sum <= 0.0:
        return 0.0
    return (positive_rank_sum - negative_rank_sum) / total_rank_sum


@dataclass(frozen=True)
class BenjaminiHochbergOutcome:
    p_values: tuple[PValue, ...]
    adjusted_p_values: tuple[PValue, ...]
    rejected: tuple[bool, ...]
    correction_applied: bool


def benjamini_hochberg_correction(
    p_values: tuple[PValue, ...], q: MetricRate
) -> BenjaminiHochbergOutcome:
    family_size = len(p_values)
    if family_size == 0:
        return BenjaminiHochbergOutcome((), (), (), correction_applied=False)
    order = sorted(range(family_size), key=lambda index: p_values[index])
    sorted_p_values = [p_values[index] for index in order]
    adjusted_sorted = [0.0] * family_size
    running_minimum = 1.0
    for rank in range(family_size, 0, -1):
        position = rank - 1
        candidate = sorted_p_values[position] * family_size / rank
        running_minimum = min(running_minimum, candidate)
        adjusted_sorted[position] = running_minimum
    adjusted = [0.0] * family_size
    for sorted_position, original_index in enumerate(order):
        adjusted[original_index] = adjusted_sorted[sorted_position]
    rejected = tuple(adjusted[index] <= q for index in range(family_size))
    return BenjaminiHochbergOutcome(
        p_values=tuple(p_values),
        adjusted_p_values=tuple(adjusted),
        rejected=rejected,
        correction_applied=family_size > 1,
    )


def cutoff_quantile(
    values: tuple[CutoffDifferenceValue, ...], quantile: MetricRate
) -> ThresholdValue:
    return float(np.quantile(np.asarray(values, dtype=np.float64), quantile, method="linear"))
