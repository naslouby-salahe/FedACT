from __future__ import annotations

from fedact.domain.assumptions import AssumptionConsequence
from fedact.domain.enums import ScientificAssumption, ScientificOutcome

SHARED_COMPONENT_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.SHARED_COMPONENT,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="cross-client feasibility and stability",
    validation="local-vs-global diagnostics",
)

INFORMATIVE_CONTROLS_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.INFORMATIVE_CONTROLS,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="matched control strata",
    validation="held-out control reconstruction",
)

CONTROL_SPAN_VALIDITY_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.CONTROL_SPAN_VALIDITY,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="calibrated/sensitivity radius",
    validation="violation sweeps",
)

PRIVATE_TRANSITION_ALLOWANCE_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.PRIVATE_TRANSITION_ALLOWANCE,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="calibrated/sensitivity allowance",
    validation="private-transition sweep",
)

HISTORICAL_PREDICTABILITY_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.HISTORICAL_PREDICTABILITY,
    failure_outcome=ScientificOutcome.INSUFFICIENT_EVIDENCE,
    operationalization="nested pseudo-future calibration",
    validation="time shuffle and pseudo-future coverage",
)

EIGENDECOMPOSITION_STABILITY_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.EIGENDECOMPOSITION_STABILITY,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="minimum eigengap criterion",
    validation="bootstrap/stability diagnostic",
)

MINIMUM_SUPPORT_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.MINIMUM_SUPPORT,
    failure_outcome=ScientificOutcome.INSUFFICIENT_EVIDENCE,
    operationalization="minimum-support gate",
    validation="support counts",
)

PLAUSIBILITY_SET_COVERAGE_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.PLAUSIBILITY_SET_COVERAGE,
    failure_outcome=ScientificOutcome.ASSUMPTION_VIOLATION,
    operationalization="pre-cutoff calibration",
    validation="radius sensitivity",
)

HONEST_PRIMARY_FEDERATION_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.HONEST_PRIMARY_FEDERATION,
    failure_outcome=ScientificOutcome.FAIL,
    operationalization="provenance/authentication",
    validation="outlier stress tests only",
)

TEMPORAL_STABILITY_CONSEQUENCE = AssumptionConsequence(
    assumption=ScientificAssumption.TEMPORAL_STABILITY,
    failure_outcome=ScientificOutcome.ABSTENTION_EXPECTED,
    operationalization="nested pseudo-future validation",
    validation="horizon calibration",
)

EXTENDED_ASSUMPTION_CONTRACTS: tuple[AssumptionConsequence, ...] = (
    SHARED_COMPONENT_CONSEQUENCE,
    INFORMATIVE_CONTROLS_CONSEQUENCE,
    CONTROL_SPAN_VALIDITY_CONSEQUENCE,
    PRIVATE_TRANSITION_ALLOWANCE_CONSEQUENCE,
    HISTORICAL_PREDICTABILITY_CONSEQUENCE,
    EIGENDECOMPOSITION_STABILITY_CONSEQUENCE,
    MINIMUM_SUPPORT_CONSEQUENCE,
    PLAUSIBILITY_SET_COVERAGE_CONSEQUENCE,
    HONEST_PRIMARY_FEDERATION_CONSEQUENCE,
    TEMPORAL_STABILITY_CONSEQUENCE,
)


FEDACT_ASSUMPTION_CONTRACTS: dict[ScientificAssumption, AssumptionConsequence] = {
    consequence.assumption: consequence for consequence in EXTENDED_ASSUMPTION_CONTRACTS
}
