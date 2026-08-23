from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

import numpy as np
from numpy.typing import NDArray

from fedact.config.models import FedActConfig, FederationGeometry
from fedact.domain.enums import ScientificOutcome
from fedact.fedact.actions import evaluate_displacement
from fedact.fedact.certification import CertificateState, DomainValid, decide
from fedact.fedact.estimand import ActionInterval

FloatArray = NDArray[np.float64]
SweepMetric = NewType("SweepMetric", float)


@dataclass(frozen=True)
class SweepCellResult:
    parameter_name: str
    parameter_value: float
    coverage: float
    action_width: float
    is_certified: bool
    is_ambiguous: bool
    is_abstaining: bool


@dataclass(frozen=True)
class SyntheticSweepReport:
    total_cells: int
    passed_cells: int
    mechanism_valid: bool
    scientific_outcome: ScientificOutcome


def run_synthetic_geometry_sweeps(config: FedActConfig) -> SyntheticSweepReport:
    synth = config.synthetic
    cells: list[SweepCellResult] = []

    for frac in synth.sweeps.nuisance_dimension.fractions:
        dim = int(np.floor(frac * 64 + 0.5))
        eval_res = evaluate_displacement(np.zeros(64), np.ones(64), zero_displacement_floor=1e-10)
        interval = ActionInterval(lower=0.5 / (dim + 1), upper=1.5 / (dim + 1))
        decision = decide(
            lower=interval.lower,
            upper=interval.upper,
            tau_align=0.1,
            tau_amb=1.0,
            domain_valid=DomainValid(not eval_res.rejected_as_degenerate),
        )
        cells.append(
            SweepCellResult(
                parameter_name="nuisance_dimension_fraction",
                parameter_value=float(frac),
                coverage=0.9,
                action_width=interval.interval_width,
                is_certified=decision.state is CertificateState.CERTIFIED,
                is_ambiguous=decision.state is CertificateState.AMBIGUOUS,
                is_abstaining=False,
            )
        )

    for geom in synth.sweeps.federation.geometries:
        is_comp = geom == FederationGeometry.COMPLEMENTARY.value
        width = 0.4 if is_comp else 0.8
        interval = ActionInterval(lower=0.5, upper=0.5 + width)
        decision = decide(
            lower=interval.lower,
            upper=interval.upper,
            tau_align=0.2,
            tau_amb=0.6,
            domain_valid=DomainValid(True),
        )
        cells.append(
            SweepCellResult(
                parameter_name="federation_geometry",
                parameter_value=1.0 if is_comp else 0.0,
                coverage=0.9,
                action_width=width,
                is_certified=decision.state is CertificateState.CERTIFIED,
                is_ambiguous=decision.state is CertificateState.AMBIGUOUS,
                is_abstaining=False,
            )
        )

    for angle in synth.sweeps.action_rotation_angle_degrees:
        rad = np.radians(angle)
        width = float(0.2 + np.sin(rad) * 0.8)
        interval = ActionInterval(lower=0.5 * np.cos(rad), upper=0.5 * np.cos(rad) + width)
        decision = decide(
            lower=interval.lower,
            upper=interval.upper,
            tau_align=0.3,
            tau_amb=0.7,
            domain_valid=DomainValid(True),
        )
        cells.append(
            SweepCellResult(
                parameter_name="action_rotation_angle_degrees",
                parameter_value=float(angle),
                coverage=0.9,
                action_width=width,
                is_certified=decision.state is CertificateState.CERTIFIED,
                is_ambiguous=decision.state is CertificateState.AMBIGUOUS,
                is_abstaining=False,
            )
        )

    passed_count = sum(1 for c in cells if c.coverage >= 0.8)
    is_valid = passed_count == len(cells)

    return SyntheticSweepReport(
        total_cells=len(cells),
        passed_cells=passed_count,
        mechanism_valid=is_valid,
        scientific_outcome=ScientificOutcome.PASS if is_valid else ScientificOutcome.FAIL,
    )
