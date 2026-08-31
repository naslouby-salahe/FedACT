from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fedact.domain.enums import (
    ArtifactBoundary,
    DatasetSplit,
    ExecutableWorkflowName,
    InformationFlowPhase,
    PartitionScheme,
    WorkflowName,
)
from fedact.domain.records import (
    ArtifactName,
    DependencyFingerprint,
    EpochIndex,
    OptionalFlag,
    RoadmapSectionId,
    TriggerabilityFlag,
    WorkflowContract,
    WorkflowDescription,
)

_WORKFLOW_CONTRACTS: tuple[WorkflowContract, ...] = (
    WorkflowContract(
        name=WorkflowName.SCIENTIFIC_AND_CONFIGURATION_AUTHORITY,
        scientific_purpose=(
            "Establish the authoritative validated configuration and locked scientific "
            "contracts consumed by every later workflow"
        ),
        required_upstream_artifacts=(ArtifactBoundary.INPUTS,),
        manipulations_and_comparators="None; authoritative configuration loading and validation"
        "only",
        metrics="Configuration schema, value, hash, and fingerprint validation results",
        applicable_statistical_analysis="Not applicable; deterministic contract validation",
        resulting_artifacts="Validated production configuration identity and configuration hash",
    ),
    WorkflowContract(
        name=WorkflowName.MATHEMATICAL_AND_NUMERICAL_VERIFICATION,
        scientific_purpose=(
            "Verify the FedACT estimand, feasible-set, propagation, certificate, and solver "
            "mathematics on analytical cases before any data-driven execution"
        ),
        required_upstream_artifacts=(ArtifactBoundary.INPUTS,),
        manipulations_and_comparators="Analytical known-truth constructions against closed-form"
        "expectations",
        metrics="Exact-set verification result, functional identifiability, width bounds,"
        "monotonicity, solver accuracy",
        applicable_statistical_analysis="Deterministic verification tolerances without sampling"
        "inference",
        resulting_artifacts="Mathematical verification completion records and residual diagnostics",
    ),
    WorkflowContract(
        name=WorkflowName.SYNTHETIC_GENERATOR_SMOKE_VALIDATION,
        scientific_purpose=(
            "Validate that the locked synthetic generator reproduces the observation model, "
            "nuisance geometry, controls, and action geometry at smoke scale"
        ),
        required_upstream_artifacts=(ArtifactBoundary.INPUTS,),
        manipulations_and_comparators="Generator outputs against locked ground-truth invariants",
        metrics="Orthogonality, intersection, spectral conditioning, and replay determinism checks",
        applicable_statistical_analysis="Deterministic invariants without sampling inference",
        resulting_artifacts="Smoke manifest and generator correctness results",
    ),
    WorkflowContract(
        name=WorkflowName.SYNTHETIC_THEORY_AND_GEOMETRY_VALIDATION,
        scientific_purpose=(
            "Validate known-truth FedACT mechanism, uncertainty, federation complementarity, "
            "and failure boundaries across the locked synthetic sweep grid"
        ),
        required_upstream_artifacts=(ArtifactBoundary.INPUTS,),
        manipulations_and_comparators=(
            "Nuisance-dimension, amplitude-mismatch, principal-angle, intersection,"
            "federation-geometry, "
            "sample-size, contamination, synchronized-nuisance, conditioning, and action-geometry"
            "sweeps"
        ),
        metrics="Known-truth set coverage, action-interval coverage, certification, ambiguity,"
        "and abstention rates",
        applicable_statistical_analysis="Locked sweep-level summaries with paired seeds as units",
        resulting_artifacts="Known-truth sweep metrics and mechanism source data",
    ),
    WorkflowContract(
        name=WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT,
        scientific_purpose=(
            "Audit real-data chronology, support, control construction, client semantics,"
            "operators, "
            "and cutoff-safe representation before any real-data training or evaluation"
        ),
        required_upstream_artifacts=(ArtifactBoundary.INPUTS,),
        manipulations_and_comparators="None; audit-only eligibility and validity assessment",
        metrics="Chronology, support, control, client-semantics, operator, and representation"
        "audit outcomes",
        applicable_statistical_analysis="Dataset eligibility decision rules without sampling"
        "inference",
        resulting_artifacts="Real-data audit manifests and dataset eligibility outcome",
    ),
    WorkflowContract(
        name=WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION,
        scientific_purpose=(
            "Reproduce identification, temporal/security, and federation baselines and validate "
            "parity against their reference implementations before confirmatory comparison"
        ),
        required_upstream_artifacts=(),
        manipulations_and_comparators="Baseline implementations against analytical and synthetic"
        "parity fixtures",
        metrics="Parity deviations against reference tolerances per baseline family",
        applicable_statistical_analysis="Tolerance-based acceptance without sampling inference",
        resulting_artifacts="Baseline checkpoints and parity manifests",
    ),
    WorkflowContract(
        name=WorkflowName.NESTED_PRE_CUTOFF_CALIBRATION,
        scientific_purpose=(
            "Select coverage, eigengap, covariance-regularization, threshold, and hardening"
            "parameters "
            "using only nested pre-cutoff pseudo-futures inside each candidate"
        ),
        required_upstream_artifacts=(),
        manipulations_and_comparators="Locked candidate grids evaluated on inner chronological"
        "pseudo-futures",
        metrics="Inner-cutoff selection criteria and candidate validity gates",
        applicable_statistical_analysis="Deterministic lexicographic candidate selection rules",
        resulting_artifacts="Selected calibration result and manifest with uncertainty and"
        "plausibility parameters",
    ),
    WorkflowContract(
        name=WorkflowName.REAL_DATA_ACTION_CERTIFICATE_VALIDATION,
        scientific_purpose=(
            "Compare certified actions against ambiguous, negative, matched point-comparator, and "
            "matched-random valid actions on exact later-real relevance outcomes"
        ),
        required_upstream_artifacts=(),
        manipulations_and_comparators=(
            "Certified actions versus ambiguity-width, negative,"
            "point-comparator-at-matched-count, "
            "and matched-random valid-action groups under defensive-effect matching"
        ),
        metrics="Certificate precision, recall, cosine future alignment, rank alignment",
        applicable_statistical_analysis="Locked paired contrasts across cutoffs with"
        "multiplicity control",
        resulting_artifacts="Action-group outcomes and certificate metric records",
    ),
    WorkflowContract(
        name=WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,
        scientific_purpose=(
            "Run the locked rolling-cutoff prospective FedACT hardening evaluation against all "
            "principal comparators under strict chronology"
        ),
        required_upstream_artifacts=(),
        manipulations_and_comparators=(
            "FedACT hardening versus static ERM, temporal invariance, future-prediction, reactive"
            "drift, "
            "adversarial-training, random-mutation, generative-augmentation, and"
            "domain-generalization baselines"
        ),
        metrics=(
            "Set/action-interval coverage, action width, certification/ambiguity/abstention rates, "
            "false-certification rate, early-horizon FNR, exposure, time-to-catch-up, clean-data"
            "degradation"
        ),
        applicable_statistical_analysis="Cutoff-clustered paired confirmatory analysis per the"
        "statistical protocol",
        resulting_artifacts="Hardened checkpoints, comparator outcomes, exposure curves, and"
        "predictive metrics",
    ),
    WorkflowContract(
        name=WorkflowName.NOVELTY_CRITICAL_ABLATIONS,
        scientific_purpose=(
            "Isolate the contribution of controls, set-valued identification, action-specific"
            "conditioning, "
            "uncertainty components, temporal modeling, and hardening through single-boundary"
            "ablations"
        ),
        required_upstream_artifacts=(),
        manipulations_and_comparators=(
            "Zeroed control evidence, point-versus-set, global-versus-action-specific,"
            "generic-robustness, "
            "uncertainty-component removals, temporal removals, action-mapping, width-gate, and"
            "hardening-off variants"
        ),
        metrics="Ablation deltas on the main prospective endpoint family",
        applicable_statistical_analysis="Paired ablation contrasts with multiplicity control",
        resulting_artifacts="Ablation outcome records per declared boundary change",
    ),
    WorkflowContract(
        name=WorkflowName.FEDERATION_AND_COMPLEMENTARITY_EVALUATION,
        scientific_purpose=(
            "Evaluate local versus federated identification, redundant versus complementary"
            "geometry, "
            "centralized equivalence, and randomized client-geometry controls"
        ),
        required_upstream_artifacts=(),
        manipulations_and_comparators=(
            "Local-only, ordinary federated, centralized-equivalent, redundant-geometry,"
            "complementary-geometry, "
            "and randomized-geometry federation conditions"
        ),
        metrics="Precision gain, identification gain, and communication cost under equal budgets",
        applicable_statistical_analysis="Paired federation contrasts with cutoff clustering",
        resulting_artifacts="Federation contrast records and geometry diagnostics",
    ),
    WorkflowContract(
        name=WorkflowName.ROBUSTNESS_AND_FAILURE_BOUNDARY_EVALUATION,
        scientific_purpose=(
            "Locate graceful-abstention versus method-failure boundaries under sparse controls,"
            "weak eigengaps, "
            "contamination, synchronized nuisance, unresolved geometry, horizon limits, and"
            "corrupted summaries"
        ),
        required_upstream_artifacts=(),
        manipulations_and_comparators=(
            "Declared stress manipulations applied to otherwise identical compatible base artifacts"
        ),
        metrics="Abstention correctness, failure classification, and boundary curves per stress"
        "family",
        applicable_statistical_analysis="Boundary-classification summaries without pooled"
        "sampling inference",
        resulting_artifacts="Failure-boundary curves and diagnostics",
    ),
    WorkflowContract(
        name=WorkflowName.CROSS_CORPUS_GENERALIZATION,
        scientific_purpose=(
            "Apply unchanged FedACT semantics to the EMBER2024 generalization study without"
            "target-corpus refitting"
        ),
        required_upstream_artifacts=(),
        manipulations_and_comparators="Source-trained artifacts transferred unchanged to the"
        "target corpus",
        metrics="Transferred coverage, certification, and security metrics on the target corpus",
        applicable_statistical_analysis="Paired transfer contrasts with cutoff clustering",
        resulting_artifacts="Cross-corpus generalization evidence",
    ),
    WorkflowContract(
        name=WorkflowName.COMMUNICATION_LIMITED_CLIENT_SELECTION,
        scientific_purpose=(
            "Select clients under equal communication budgets using D-optimal action weights"
            "against "
            "random, largest-sample, global-information, and interval-contraction selectors"
        ),
        required_upstream_artifacts=(),
        manipulations_and_comparators=(
            "D-optimal selection versus random, largest-sample-count, global-information, "
            "and action-interval-contraction comparators at each budget fraction"
        ),
        metrics="Budget-matched identification and certification outcomes per selector",
        applicable_statistical_analysis="Paired selector contrasts across budget fractions",
        resulting_artifacts="Client-selection outcome records",
    ),
    WorkflowContract(
        name=WorkflowName.STATISTICAL_SYNTHESIS,
        scientific_purpose=(
            "Execute the locked confirmatory contrasts, sensitivity analyses, multiplicity"
            "correction, "
            "and claim-state adjudication over verified full-precision evaluation evidence"
        ),
        required_upstream_artifacts=(),
        manipulations_and_comparators="Prespecified paired contrasts and locked sensitivity"
        "surfaces",
        metrics="Effect sizes, confidence intervals, p-values, adjusted significance, claim states",
        applicable_statistical_analysis="Cutoff-clustered BCa bootstrap, Wilcoxon, rank-biserial"
        "effects, BH correction",
        resulting_artifacts="Paired contrasts, bootstrap objects, tests, multiplicity results,"
        "sensitivity summaries, claim inputs",
    ),
    WorkflowContract(
        name=WorkflowName.MANUSCRIPT_EVIDENCE_GENERATION,
        scientific_purpose=(
            "Export verified manuscript tables, figures, appendix evidence, and reproducibility"
            "evidence "
            "without recomputation"
        ),
        required_upstream_artifacts=(),
        manipulations_and_comparators="None; pure export from verified analysis artifacts",
        metrics="Presentation-formatted values derived from verified full-precision evidence",
        applicable_statistical_analysis="Reporting of completed locked analyses only",
        resulting_artifacts="Figures, tables, compact metrics/statistics evidence,"
        "reproducibility evidence, evidence index",
    ),
)

WORKFLOW_CONTRACTS: dict[WorkflowName, WorkflowContract] = {
    contract.name: contract for contract in _WORKFLOW_CONTRACTS
}

OPTIONAL_WORKFLOW_NAMES: frozenset[WorkflowName] = frozenset(
    {WorkflowName.COMMUNICATION_LIMITED_CLIENT_SELECTION}
)


def workflow_contract(name: WorkflowName) -> WorkflowContract:
    return WORKFLOW_CONTRACTS[name]


@dataclass(frozen=True)
class RegisteredWorkflow:
    name: ExecutableWorkflowName
    roadmap_section: RoadmapSectionId
    dependencies: tuple[ExecutableWorkflowName, ...]
    optional: OptionalFlag
    description: WorkflowDescription

    @property
    def required_dependencies(self) -> tuple[ExecutableWorkflowName, ...]:
        return self.dependencies


WORKFLOW_REGISTRY: tuple[RegisteredWorkflow, ...] = (
    RegisteredWorkflow(
        name=ExecutableWorkflowName.PREPROCESS,
        roadmap_section="§10",
        dependencies=(),
        optional=False,
        description="Dataset preparation, cutoff construction, preprocessing, and real-data audits",
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.SMOKE,
        roadmap_section="§21",
        dependencies=(),
        optional=False,
        description="Synthetic generator smoke validation",
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.BASELINE_PARITY,
        roadmap_section="§14",
        dependencies=(ExecutableWorkflowName.PREPROCESS,),
        optional=False,
        description="Baseline chronology, budget, and implementation parity verification",
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.NESTED_CALIBRATION,
        roadmap_section="§25",
        dependencies=(
            ExecutableWorkflowName.PREPROCESS,
            ExecutableWorkflowName.BASELINE_PARITY,
        ),
        optional=False,
        description="Nested pre-cutoff calibration of certification and hardening parameters",
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.MATH_VERIFICATION,
        roadmap_section="§13",
        dependencies=(),
        optional=False,
        description="Closed-form solver, feasible set, and theoretical bound verification",
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.SYNTHETIC_GEOMETRY,
        roadmap_section="§21",
        dependencies=(
            ExecutableWorkflowName.MATH_VERIFICATION,
            ExecutableWorkflowName.SMOKE,
        ),
        optional=False,
        description="Sweeps over synthetic nuisance geometry, rank, and uncertainty radii",
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION,
        roadmap_section="§26",
        dependencies=(
            ExecutableWorkflowName.PREPROCESS,
            ExecutableWorkflowName.BASELINE_PARITY,
            ExecutableWorkflowName.NESTED_CALIBRATION,
        ),
        optional=False,
        description=(
            "Empirical validation of action certificate precision on real-world "
            "malformed and benign samples"
        ),
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
        roadmap_section="§27",
        dependencies=(ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION,),
        optional=False,
        description=(
            "Main chronological prospective evaluation of hardened FedACT "
            "detectors against baselines"
        ),
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.ABLATIONS,
        roadmap_section="§28",
        dependencies=(ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
        optional=False,
        description=(
            "Novelty-critical component ablations (no controls, point vs set, "
            "global vs local, temporal)"
        ),
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.FEDERATION,
        roadmap_section="§29",
        dependencies=(ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
        optional=False,
        description=(
            "Multi-client federation geometry: redundant vs complementary information structures"
        ),
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.FAILURE_BOUNDARIES,
        roadmap_section="§30",
        dependencies=(ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
        optional=False,
        description=(
            "Empirical stress testing and failure boundary characterization "
            "under severe distribution shifts"
        ),
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.CROSS_CORPUS,
        roadmap_section="§31",
        dependencies=(
            ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
            ExecutableWorkflowName.FAILURE_BOUNDARIES,
            ExecutableWorkflowName.PREPROCESS,
        ),
        optional=False,
        description="Cross-corpus transfer evaluation between PE and APK ecosystems",
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.CLIENT_SELECTION,
        roadmap_section="§32",
        dependencies=(ExecutableWorkflowName.FEDERATION,),
        optional=True,
        description="Greedy D-optimal client selection under communication constraints",
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.STATISTICAL_SYNTHESIS,
        roadmap_section="§33",
        dependencies=(
            ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION,
            ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
            ExecutableWorkflowName.ABLATIONS,
            ExecutableWorkflowName.FEDERATION,
            ExecutableWorkflowName.FAILURE_BOUNDARIES,
            ExecutableWorkflowName.CROSS_CORPUS,
        ),
        optional=False,
        description=(
            "Statistical meta-analysis, FDR correction, and automated scientific verdict generation"
        ),
    ),
)

REGISTRY_NAMES: dict[ExecutableWorkflowName, RegisteredWorkflow] = {
    workflow.name: workflow for workflow in WORKFLOW_REGISTRY
}


def registered_workflow(name: ExecutableWorkflowName) -> RegisteredWorkflow:
    if name in REGISTRY_NAMES:
        return REGISTRY_NAMES[name]
    raise KeyError(f"Workflow {name.value} not registered in scientific registry")


CLI_SELECTABLE_WORKFLOWS: tuple[ExecutableWorkflowName, ...] = tuple(
    workflow.name for workflow in WORKFLOW_REGISTRY
)

WORKFLOW_ORDER: tuple[WorkflowName, ...] = (
    WorkflowName.SCIENTIFIC_AND_CONFIGURATION_AUTHORITY,
    WorkflowName.MATHEMATICAL_AND_NUMERICAL_VERIFICATION,
    WorkflowName.SYNTHETIC_GENERATOR_SMOKE_VALIDATION,
    WorkflowName.SYNTHETIC_THEORY_AND_GEOMETRY_VALIDATION,
    WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT,
    WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION,
    WorkflowName.NESTED_PRE_CUTOFF_CALIBRATION,
    WorkflowName.REAL_DATA_ACTION_CERTIFICATE_VALIDATION,
    WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,
    WorkflowName.NOVELTY_CRITICAL_ABLATIONS,
    WorkflowName.FEDERATION_AND_COMPLEMENTARITY_EVALUATION,
    WorkflowName.ROBUSTNESS_AND_FAILURE_BOUNDARY_EVALUATION,
    WorkflowName.CROSS_CORPUS_GENERALIZATION,
    WorkflowName.COMMUNICATION_LIMITED_CLIENT_SELECTION,
    WorkflowName.STATISTICAL_SYNTHESIS,
    WorkflowName.MANUSCRIPT_EVIDENCE_GENERATION,
)

_REAL_DATA_PREREQUISITES: tuple[WorkflowName, ...] = (
    WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT,
    WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION,
    WorkflowName.NESTED_PRE_CUTOFF_CALIBRATION,
)

_WORKFLOW_PREREQUISITES: dict[WorkflowName, tuple[WorkflowName, ...]] = {
    WorkflowName.SCIENTIFIC_AND_CONFIGURATION_AUTHORITY: (),
    WorkflowName.MATHEMATICAL_AND_NUMERICAL_VERIFICATION: (
        WorkflowName.SCIENTIFIC_AND_CONFIGURATION_AUTHORITY,
    ),
    WorkflowName.SYNTHETIC_GENERATOR_SMOKE_VALIDATION: (
        WorkflowName.MATHEMATICAL_AND_NUMERICAL_VERIFICATION,
    ),
    WorkflowName.SYNTHETIC_THEORY_AND_GEOMETRY_VALIDATION: (
        WorkflowName.SYNTHETIC_GENERATOR_SMOKE_VALIDATION,
    ),
    WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT: (
        WorkflowName.SYNTHETIC_THEORY_AND_GEOMETRY_VALIDATION,
    ),
    WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION: (
        WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT,
    ),
    WorkflowName.NESTED_PRE_CUTOFF_CALIBRATION: (
        WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION,
    ),
    WorkflowName.REAL_DATA_ACTION_CERTIFICATE_VALIDATION: _REAL_DATA_PREREQUISITES,
    WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION: _REAL_DATA_PREREQUISITES,
    WorkflowName.NOVELTY_CRITICAL_ABLATIONS: (WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,),
    WorkflowName.FEDERATION_AND_COMPLEMENTARITY_EVALUATION: (
        WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,
    ),
    WorkflowName.ROBUSTNESS_AND_FAILURE_BOUNDARY_EVALUATION: (
        WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,
    ),
    WorkflowName.CROSS_CORPUS_GENERALIZATION: (WorkflowName.MAIN_PROSPECTIVE_FEDACT_EVALUATION,),
    WorkflowName.COMMUNICATION_LIMITED_CLIENT_SELECTION: (
        WorkflowName.FEDERATION_AND_COMPLEMENTARITY_EVALUATION,
    ),
    WorkflowName.STATISTICAL_SYNTHESIS: (
        WorkflowName.NOVELTY_CRITICAL_ABLATIONS,
        WorkflowName.FEDERATION_AND_COMPLEMENTARITY_EVALUATION,
        WorkflowName.ROBUSTNESS_AND_FAILURE_BOUNDARY_EVALUATION,
        WorkflowName.CROSS_CORPUS_GENERALIZATION,
        WorkflowName.REAL_DATA_ACTION_CERTIFICATE_VALIDATION,
    ),
    WorkflowName.MANUSCRIPT_EVIDENCE_GENERATION: (WorkflowName.STATISTICAL_SYNTHESIS,),
}

WORKFLOW_PREREQUISITES: dict[WorkflowName, tuple[WorkflowName, ...]] = {
    name: _WORKFLOW_PREREQUISITES[name] for name in WORKFLOW_ORDER
}


def validate_workflow_prerequisite_graph() -> None:
    position = {name: index for index, name in enumerate(WORKFLOW_ORDER)}
    if len(position) != len(WORKFLOW_ORDER):
        raise ValueError("workflow order contains duplicate workflows")
    for name, prerequisites in WORKFLOW_PREREQUISITES.items():
        for prerequisite in prerequisites:
            if position[prerequisite] >= position[name]:
                raise ValueError(f"prerequisite {prerequisite} does not precede {name}")


class SharedProducer(StrEnum):
    REPRESENTATION_DETECTOR_FIT = "representation_detector_fit"
    ENCODING_SCORING_AND_SUMMARIES = "encoding_scoring_and_summaries"
    NESTED_PRE_CUTOFF_CALIBRATION = "nested_pre_cutoff_calibration"
    BASELINE_FIT_PARITY = "baseline_fit_parity"


class OverwriteRequest:
    def __init__(self, requested: bool = False) -> None:
        self.requested = requested


class ReuseDecision(StrEnum):
    REUSE = "REUSE"
    STALE = "STALE"
    OVERWRITE = "OVERWRITE"
    RECOMPUTE = "RECOMPUTE"


@dataclass(frozen=True)
class PreprocessStage:
    stage_order: EpochIndex
    name: ArtifactName
    scope: WorkflowDescription


@dataclass(frozen=True)
class ProducerOwnership:
    boundary: ArtifactBoundary
    sole_producer: WorkflowName
    reuse_scope: WorkflowDescription
    phase: InformationFlowPhase
    partition_scheme: PartitionScheme
    split_eligibility: tuple[DatasetSplit, ...]

    @property
    def producer(self) -> WorkflowName:
        return self.sole_producer


_PREPROCESS_STAGE_DEFINITIONS: tuple[tuple[ArtifactName, WorkflowDescription], ...] = (
    ("raw discovery/checksum", "raw-data-manifests"),
    ("normalized parsed preparation", "parsed-samples"),
    ("chronology/cutoff construction", "chronological-and-federated-splits"),
    ("real-data audits", "audit-manifests"),
)
PREPROCESS_STAGE_FLOW: tuple[PreprocessStage, ...] = tuple(
    PreprocessStage(stage_order=index, name=name, scope=scope)
    for index, (name, scope) in enumerate(_PREPROCESS_STAGE_DEFINITIONS, start=1)
)


PREPROCESS_OWNED_BOUNDARIES: dict[ArtifactBoundary, ProducerOwnership] = {
    ArtifactBoundary.DATASET_PREPARATION: ProducerOwnership(
        boundary=ArtifactBoundary.DATASET_PREPARATION,
        sole_producer=WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT,
        reuse_scope="raw-data-manifests",
        phase=InformationFlowPhase.PREPROCESSING,
        partition_scheme=PartitionScheme.CHRONOLOGICAL,
        split_eligibility=(DatasetSplit.HISTORICAL, DatasetSplit.PROSPECTIVE),
    ),
    ArtifactBoundary.PREPROCESSING_AND_SPLITS: ProducerOwnership(
        boundary=ArtifactBoundary.PREPROCESSING_AND_SPLITS,
        sole_producer=WorkflowName.REAL_DATA_FEASIBILITY_AND_CONTROL_AUDIT,
        reuse_scope="preprocessing-and-splits",
        phase=InformationFlowPhase.PREPROCESSING,
        partition_scheme=PartitionScheme.FEDERATED,
        split_eligibility=(DatasetSplit.HISTORICAL, DatasetSplit.PROSPECTIVE),
    ),
}


def is_preprocess_triggerable(key: SharedProducer | ArtifactBoundary) -> TriggerabilityFlag:
    if isinstance(key, SharedProducer):
        return key == SharedProducer.REPRESENTATION_DETECTOR_FIT
    return key in PREPROCESS_OWNED_BOUNDARIES


def ownership_for(key: SharedProducer | ArtifactBoundary) -> ProducerOwnership:
    if isinstance(key, SharedProducer):
        if key is SharedProducer.REPRESENTATION_DETECTOR_FIT:
            return ProducerOwnership(
                boundary=ArtifactBoundary.TRAINING_CHECKPOINTS,
                sole_producer=WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION,
                reuse_scope="representation and base detector fit",
                phase=InformationFlowPhase.HISTORICAL_CALIBRATION,
                partition_scheme=PartitionScheme.CHRONOLOGICAL,
                split_eligibility=(DatasetSplit.HISTORICAL,),
            )
        if key is SharedProducer.ENCODING_SCORING_AND_SUMMARIES:
            return ProducerOwnership(
                boundary=ArtifactBoundary.SCORING_AND_SUMMARIES,
                sole_producer=WorkflowName.NESTED_PRE_CUTOFF_CALIBRATION,
                reuse_scope="same checkpoint encoded and scored observations",
                phase=InformationFlowPhase.HISTORICAL_CALIBRATION,
                partition_scheme=PartitionScheme.FEDERATED,
                split_eligibility=(DatasetSplit.HISTORICAL,),
            )
        if key is SharedProducer.NESTED_PRE_CUTOFF_CALIBRATION:
            return ProducerOwnership(
                boundary=ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
                sole_producer=WorkflowName.NESTED_PRE_CUTOFF_CALIBRATION,
                reuse_scope="dataset/cutoff nested pre-cutoff calibration",
                phase=InformationFlowPhase.HISTORICAL_CALIBRATION,
                partition_scheme=PartitionScheme.FEDERATED,
                split_eligibility=(DatasetSplit.HISTORICAL,),
            )
        return ProducerOwnership(
            boundary=ArtifactBoundary.TRAINING_CHECKPOINTS,
            sole_producer=WorkflowName.BASELINE_REPRODUCTION_AND_PARITY_VALIDATION,
            reuse_scope="baseline fit parity",
            phase=InformationFlowPhase.HISTORICAL_CALIBRATION,
            partition_scheme=PartitionScheme.CHRONOLOGICAL,
            split_eligibility=(DatasetSplit.HISTORICAL,),
        )
    if key in PREPROCESS_OWNED_BOUNDARIES:
        return PREPROCESS_OWNED_BOUNDARIES[key]
    raise KeyError(f"No producer registered for {key}")


def resolve_reuse_or_recompute(
    existing_fingerprint: DependencyFingerprint | None,
    expected_fingerprint: DependencyFingerprint,
    overwrite_request: OverwriteRequest,
) -> ReuseDecision:
    if overwrite_request.requested:
        return ReuseDecision.OVERWRITE
    if existing_fingerprint is None or existing_fingerprint != expected_fingerprint:
        return ReuseDecision.STALE
    return ReuseDecision.REUSE


__all__ = [
    "CLI_SELECTABLE_WORKFLOWS",
    "OPTIONAL_WORKFLOW_NAMES",
    "PREPROCESS_OWNED_BOUNDARIES",
    "PREPROCESS_STAGE_FLOW",
    "REGISTRY_NAMES",
    "ReuseDecision",
    "SharedProducer",
    "WORKFLOW_CONTRACTS",
    "WORKFLOW_ORDER",
    "WORKFLOW_PREREQUISITES",
    "WORKFLOW_REGISTRY",
    "is_preprocess_triggerable",
    "ownership_for",
    "registered_workflow",
    "resolve_reuse_or_recompute",
    "validate_workflow_prerequisite_graph",
    "workflow_contract",
]
