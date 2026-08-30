from __future__ import annotations

import numpy as np
import pytest

from fedact.domain.enums import ScientificAssumption, ScientificOutcome
from fedact.fedact.contracts import (
    CONTROL_SPAN_VALIDITY_CONSEQUENCE,
    EXTENDED_ASSUMPTION_CONTRACTS,
    FEDACT_ASSUMPTION_CONTRACTS,
    INFORMATIVE_CONTROLS_CONSEQUENCE,
    PRIVATE_TRANSITION_ALLOWANCE_CONSEQUENCE,
    SHARED_COMPONENT_CONSEQUENCE,
)
from fedact.fedact.transitions import (
    AbstentionReason,
    effective_support,
    geometric_median,
    later_real_proxy,
    observed_nuisance_amplitude,
    weighted_control_center,
)


@pytest.mark.parametrize(
    ("consequence", "assumption"),
    [
        (SHARED_COMPONENT_CONSEQUENCE, ScientificAssumption.SHARED_COMPONENT),
        (INFORMATIVE_CONTROLS_CONSEQUENCE, ScientificAssumption.INFORMATIVE_CONTROLS),
        (CONTROL_SPAN_VALIDITY_CONSEQUENCE, ScientificAssumption.CONTROL_SPAN_VALIDITY),
        (
            PRIVATE_TRANSITION_ALLOWANCE_CONSEQUENCE,
            ScientificAssumption.PRIVATE_TRANSITION_ALLOWANCE,
        ),
    ],
)
def test_assumption_contracts_register_into_the_domain_table(
    consequence: object, assumption: ScientificAssumption
) -> None:
    assert FEDACT_ASSUMPTION_CONTRACTS[assumption] is consequence


def test_every_section_six_assumption_now_has_an_executable_contract() -> None:
    covered = {consequence.assumption for consequence in EXTENDED_ASSUMPTION_CONTRACTS}
    expected = {
        ScientificAssumption.SHARED_COMPONENT,
        ScientificAssumption.INFORMATIVE_CONTROLS,
        ScientificAssumption.CONTROL_SPAN_VALIDITY,
        ScientificAssumption.PRIVATE_TRANSITION_ALLOWANCE,
        ScientificAssumption.HISTORICAL_PREDICTABILITY,
        ScientificAssumption.EIGENDECOMPOSITION_STABILITY,
        ScientificAssumption.MINIMUM_SUPPORT,
        ScientificAssumption.PLAUSIBILITY_SET_COVERAGE,
        ScientificAssumption.HONEST_PRIMARY_FEDERATION,
        ScientificAssumption.TEMPORAL_STABILITY,
    }
    assert covered == expected


def test_honest_federation_failure_is_a_scientific_fail_not_abstention() -> None:
    from fedact.fedact.contracts import FEDACT_ASSUMPTION_CONTRACTS

    contract = FEDACT_ASSUMPTION_CONTRACTS[ScientificAssumption.HONEST_PRIMARY_FEDERATION]
    assert contract.failure_outcome is ScientificOutcome.FAIL


def test_effective_support_matches_the_roadmap_harmonic_definition() -> None:
    assert effective_support(100, 100) == pytest.approx(50.0)
    assert effective_support(50, 200) == pytest.approx(40.0)


def test_weighted_control_center_weights_by_effective_support() -> None:
    low = np.array([1.0, 0.0])
    high = np.array([0.0, 1.0])
    center = weighted_control_center((low, high), ((10, 10), (1000, 1000)))
    assert center[1] > center[0]


def test_geometric_median_converges_and_handles_exact_point() -> None:
    points = np.array([[0.0, 0.0], [4.0, 0.0], [2.0, 3.0]])
    median = geometric_median(points, tolerance=1e-9, maximum_iterations=500)
    assert median.shape == (2,)
    single = np.array([[5.0, 5.0]])
    at_observation = geometric_median(single, tolerance=1e-9, maximum_iterations=50)
    assert at_observation[0] == pytest.approx(5.0)


def test_observed_nuisance_amplitude_quantile() -> None:
    displacements = (np.array([1.0]), np.array([2.0]), np.array([3.0]))
    amplitude = observed_nuisance_amplitude(displacements, quantile=0.95, supports=((10, 10),) * 3)
    assert amplitude >= 0.0


def test_abstention_reasons_are_the_exact_locked_vocabulary() -> None:
    assert {reason.value for reason in AbstentionReason} == {
        "ABSTAIN_NO_USABLE_CONTROL",
        "ABSTAIN_INSUFFICIENT_MALICIOUS_SUPPORT",
        "ABSTAIN_INSUFFICIENT_CONTROL_SUPPORT",
        "ABSTAIN_INSUFFICIENT_PRIVATE_ALLOWANCE_HISTORY",
        "ABSTAIN_UNSTABLE_NUISANCE_RANK",
        "ABSTAIN_WEAK_EIGENGAP",
        "ABSTAIN_CONTROL_RECONSTRUCTION_FAILURE",
        "ABSTAIN_FEASIBLE_SET_INCONSISTENT",
        "ABSTAIN_INSUFFICIENT_TEMPORAL_HISTORY",
        "ABSTAIN_FORECAST_SET_TOO_WIDE",
        "ABSTAIN_NO_CERTIFIED_ACTION",
        "ABSTAIN_OPERATOR_COVERAGE_INSUFFICIENT",
        "ABSTAIN_SYNCHRONIZED_NUISANCE_RISK",
        "ABSTAIN_SINGLE_CLIENT_CERTIFICATE_DOMINANCE",
    }


def test_later_real_proxy_is_effective_support_weighted_displacement() -> None:
    pre = (np.zeros(2), np.zeros(2))
    post = (np.array([1.0, 0.0]), np.array([0.0, 1.0]))
    proxy = later_real_proxy(
        pre_means=pre,
        post_means=post,
        pre_supports=(100, 100),
        post_supports=(100, 400),
    )
    assert proxy[1] > proxy[0]
