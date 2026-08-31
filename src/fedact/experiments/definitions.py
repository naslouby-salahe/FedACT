from __future__ import annotations

from dataclasses import dataclass

from fedact.domain.enums import ArtifactBoundary, ExecutableWorkflowName, WorkflowName
from fedact.domain.records import (
    OptionalFlag,
    RoadmapSectionId,
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
        required_upstream_artifacts=(
            ArtifactBoundary.INPUTS,
            ArtifactBoundary.SCORING_AND_SUMMARIES,
        ),
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
        required_upstream_artifacts=(
            ArtifactBoundary.INPUTS,
            ArtifactBoundary.DATASET_PREPARATION,
            ArtifactBoundary.PREPROCESSING_AND_SPLITS,
        ),
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
        required_upstream_artifacts=(
            ArtifactBoundary.PREPROCESSING_AND_SPLITS,
            ArtifactBoundary.TRAINING_CHECKPOINTS,
        ),
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
        required_upstream_artifacts=(
            ArtifactBoundary.PREPROCESSING_AND_SPLITS,
            ArtifactBoundary.TRAINING_CHECKPOINTS,
            ArtifactBoundary.SCORING_AND_SUMMARIES,
        ),
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
        required_upstream_artifacts=(
            ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
            ArtifactBoundary.SCORING_AND_SUMMARIES,
        ),
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
        required_upstream_artifacts=(
            ArtifactBoundary.TRAINING_CHECKPOINTS,
            ArtifactBoundary.SCORING_AND_SUMMARIES,
            ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
        ),
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
        required_upstream_artifacts=(
            ArtifactBoundary.TRAINING_CHECKPOINTS,
            ArtifactBoundary.SCORING_AND_SUMMARIES,
            ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
        ),
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
        required_upstream_artifacts=(
            ArtifactBoundary.TRAINING_CHECKPOINTS,
            ArtifactBoundary.SCORING_AND_SUMMARIES,
            ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
        ),
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
        required_upstream_artifacts=(
            ArtifactBoundary.TRAINING_CHECKPOINTS,
            ArtifactBoundary.SCORING_AND_SUMMARIES,
            ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
        ),
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
        required_upstream_artifacts=(
            ArtifactBoundary.PREPROCESSING_AND_SPLITS,
            ArtifactBoundary.TRAINING_CHECKPOINTS,
            ArtifactBoundary.SCORING_AND_SUMMARIES,
            ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
        ),
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
        required_upstream_artifacts=(
            ArtifactBoundary.SCORING_AND_SUMMARIES,
            ArtifactBoundary.CALIBRATION_AND_CERTIFICATION,
        ),
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
        required_upstream_artifacts=(ArtifactBoundary.EVALUATION,),
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
        required_upstream_artifacts=(ArtifactBoundary.ANALYSIS,),
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
