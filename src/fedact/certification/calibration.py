from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

import torch
from pydantic import Field

from fedact.certification.certificate import (
    DomainValid,
    build_nuisance_spaces,
    certify_action_interval,
)
from fedact.certification.uncertainty import (
    estimate_client_nuisance_subspace,
    solve_action_interval,
)
from fedact.domain.types import (
    CertificationStatus,
    DegradationValue,
    DetailMessage,
    MetricRate,
    PercentileValue,
    RankDimension,
    RankSelectionMethod,
    ThresholdValue,
)
from fedact.learning.representation import EMBEDDING_DIMENSION

_CLIENT_CONTROL_ROWS = 20
_CERTIFICATION_DRAW_COUNT = 30


@dataclass(frozen=True)
class HardeningWeightDegradation:
    hardening_weight: ThresholdValue
    clean_degradation: DegradationValue


@dataclass(frozen=True)
class HardeningWeightDegradations:
    entries: tuple[HardeningWeightDegradation, ...]

    def for_weight(self, hardening_weight: ThresholdValue) -> DegradationValue:
        for entry in self.entries:
            if entry.hardening_weight == hardening_weight:
                return entry.clean_degradation
        raise KeyError(f"no clean degradation recorded for hardening weight {hardening_weight}")


@dataclass(frozen=True)
class CalibrationCandidate:
    candidate_id: DetailMessage
    tau_align: ThresholdValue
    tau_amb: ThresholdValue
    hardening_weight: ThresholdValue
    observed_coverage: MetricRate
    observed_certification_rate: MetricRate
    clean_degradation: DegradationValue


def _certification_rate(
    maximum_nuisance_rank: RankDimension,
    eigengap_regularization: ThresholdValue,
    scale_standardization_floor: ThresholdValue,
    historical_realized_diameter_quantile: MetricRate,
    tau_align: ThresholdValue,
    tau_amb: ThresholdValue,
) -> MetricRate:
    latent_dim = EMBEDDING_DIMENSION
    estimate = estimate_client_nuisance_subspace(
        client_controls=torch.randn(_CLIENT_CONTROL_ROWS, latent_dim),
        rank_selection=RankSelectionMethod.FIXED_RANK,
        fixed_rank=maximum_nuisance_rank,
        eigengap_regularization=eigengap_regularization,
        scale_standardization_floor=scale_standardization_floor,
    )
    feasible_set = build_nuisance_spaces(
        nuisance_subspaces=(estimate.subspace,),
        uncertainty_radii=(estimate.uncertainty_radius,),
    )
    certified = 0
    for _unused in range(_CERTIFICATION_DRAW_COUNT):
        action = torch.randn(latent_dim)
        interval = solve_action_interval(action_vector=action, feasible_set=feasible_set)
        decision = certify_action_interval(
            action_interval=interval,
            domain_validity=DomainValid(valid=True),
            alignment_threshold=tau_align,
            ambiguity_width_threshold=tau_amb,
            set_diameter=feasible_set.diameter,
            historical_realized_diameter_quantile=historical_realized_diameter_quantile,
        )
        if decision.status is CertificationStatus.CERTIFIED_POSITIVE:
            certified += 1
    return certified / _CERTIFICATION_DRAW_COUNT


def generate_calibration_candidates(
    alignment_percentile_candidates: tuple[PercentileValue, ...],
    ambiguity_width_percentile_candidates: tuple[PercentileValue, ...],
    hardening_weight_candidates: tuple[ThresholdValue, ...],
    maximum_nuisance_rank: RankDimension,
    eigengap_regularization: ThresholdValue,
    scale_standardization_floor: ThresholdValue,
    historical_realized_diameter_quantile: MetricRate,
    clean_degradations: HardeningWeightDegradations,
) -> tuple[CalibrationCandidate, ...]:
    align_grid = tuple(value / 100.0 for value in alignment_percentile_candidates)
    ambiguity_grid = tuple(value / 100.0 for value in ambiguity_width_percentile_candidates)
    weight_grid = hardening_weight_candidates

    certification_rates = {
        (tau_align, tau_amb): _certification_rate(
            maximum_nuisance_rank,
            eigengap_regularization,
            scale_standardization_floor,
            historical_realized_diameter_quantile,
            tau_align,
            tau_amb,
        )
        for tau_align in align_grid
        for tau_amb in ambiguity_grid
    }

    candidates: list[CalibrationCandidate] = []
    idx = 0
    for tau_align in align_grid:
        for tau_amb in ambiguity_grid:
            rate = certification_rates[(tau_align, tau_amb)]
            for weight in weight_grid:
                candidates.append(
                    CalibrationCandidate(
                        candidate_id=f"cand_{idx}",
                        tau_align=tau_align,
                        tau_amb=tau_amb,
                        hardening_weight=weight,
                        observed_coverage=rate,
                        observed_certification_rate=rate,
                        clean_degradation=clean_degradations.for_weight(weight),
                    )
                )
                idx += 1
    return tuple(candidates)


CoverageThreshold = Annotated[float, Field(ge=0.0, le=1.0)]
DegradationBound = Annotated[float, Field(ge=0.0)]


class CalibrationSelectionError(ValueError):
    pass


@dataclass(frozen=True)
class SelectedCalibration:
    selected_candidate: CalibrationCandidate
    selection_rank: RankDimension


def select_best_calibration_candidate(
    candidates: tuple[CalibrationCandidate, ...],
    target_coverage: CoverageThreshold,
    max_clean_degradation: DegradationBound,
) -> SelectedCalibration:
    valid = [
        c
        for c in candidates
        if c.observed_coverage >= target_coverage and c.clean_degradation <= max_clean_degradation
    ]
    if not valid:
        raise CalibrationSelectionError(
            "no calibration candidate satisfies coverage and clean cost gates"
        )
    sorted_candidates = sorted(
        valid,
        key=lambda c: (-c.observed_certification_rate, c.clean_degradation, c.candidate_id),
    )
    return SelectedCalibration(
        selected_candidate=sorted_candidates[0],
        selection_rank=1,
    )


class CalibrationValidationError(ValueError):
    pass


def validate_calibration_outcome(
    selected: SelectedCalibration, minimum_coverage: CoverageThreshold
) -> None:
    if selected.selected_candidate.observed_coverage < minimum_coverage:
        raise CalibrationValidationError(
            "selected candidate coverage below empirical validity limit"
        )
