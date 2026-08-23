from __future__ import annotations

from dataclasses import dataclass

from fedact.domain.enums import ExecutableWorkflowName


@dataclass(frozen=True)
class RegisteredWorkflow:
    name: ExecutableWorkflowName
    roadmap_section: str
    required_dependencies: tuple[ExecutableWorkflowName, ...]
    optional: bool
    description: str


WORKFLOW_REGISTRY: tuple[RegisteredWorkflow, ...] = (
    RegisteredWorkflow(
        name=ExecutableWorkflowName.MATH_VERIFICATION,
        roadmap_section="§20 Mathematical and Numerical Verification",
        required_dependencies=(),
        optional=False,
        description=(
            "Exact-set, identifiability, support-bound, monotonicity, solver, degeneracy, "
            "and infeasibility verification on analytical cases"
        ),
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.SYNTHETIC_GEOMETRY,
        roadmap_section="§22 Synthetic Theory and Geometry Validation",
        required_dependencies=(
            ExecutableWorkflowName.MATH_VERIFICATION,
            ExecutableWorkflowName.SMOKE,
        ),
        optional=False,
        description="Locked known-truth geometry, uncertainty, sample-size, conditioning sweeps",
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION,
        roadmap_section="§26 Real-Data Action-Certificate Validation",
        required_dependencies=(
            ExecutableWorkflowName.PREPROCESS,
            ExecutableWorkflowName.BASELINE_PARITY,
            ExecutableWorkflowName.NESTED_CALIBRATION,
        ),
        optional=False,
        description=(
            "Later-real comparison of certified, ambiguous, negative, matched-random actions"
        ),
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
        roadmap_section="§27 Main Prospective FedACT Evaluation",
        required_dependencies=(ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION,),
        optional=False,
        description="Rolling-cutoff prospective hardening evaluation against principal comparators",
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.ABLATIONS,
        roadmap_section="§28 Novelty-Critical Ablations",
        required_dependencies=(ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
        optional=False,
        description="Single-boundary novelty-critical ablation outcomes",
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.FEDERATION,
        roadmap_section="§29 Federation and Complementarity Evaluation",
        required_dependencies=(ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
        optional=False,
        description="Local/federated, redundant/complementary, centralized-equivalence contrasts",
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.FAILURE_BOUNDARIES,
        roadmap_section="§30 Robustness and Failure-Boundary Evaluation",
        required_dependencies=(ExecutableWorkflowName.PROSPECTIVE_EVALUATION,),
        optional=False,
        description=(
            "Graceful-abstention versus failure boundaries under declared stress manipulations"
        ),
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.CROSS_CORPUS,
        roadmap_section="§31 Cross-Corpus Generalization",
        required_dependencies=(
            ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
            ExecutableWorkflowName.FAILURE_BOUNDARIES,
            ExecutableWorkflowName.PREPROCESS,
        ),
        optional=False,
        description="Unchanged FedACT semantics applied to the secondary corpus",
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.CLIENT_SELECTION,
        roadmap_section="§32 Communication-Limited Client Selection",
        required_dependencies=(ExecutableWorkflowName.FEDERATION,),
        optional=True,
        description="Equal-budget D-optimal client selection versus locked comparators",
    ),
    RegisteredWorkflow(
        name=ExecutableWorkflowName.STATISTICAL_SYNTHESIS,
        roadmap_section="§33 Statistical Synthesis and Sensitivity Analysis",
        required_dependencies=(
            ExecutableWorkflowName.ACTION_CERTIFICATE_VALIDATION,
            ExecutableWorkflowName.PROSPECTIVE_EVALUATION,
            ExecutableWorkflowName.ABLATIONS,
            ExecutableWorkflowName.FEDERATION,
            ExecutableWorkflowName.FAILURE_BOUNDARIES,
            ExecutableWorkflowName.CROSS_CORPUS,
        ),
        optional=False,
        description="Confirmatory contrasts, sensitivity surfaces, multiplicity, claim states",
    ),
)

REGISTRY_NAMES: dict[ExecutableWorkflowName, RegisteredWorkflow] = {
    workflow.name: workflow for workflow in WORKFLOW_REGISTRY
}
CLI_SELECTABLE_WORKFLOWS: frozenset[ExecutableWorkflowName] = frozenset(REGISTRY_NAMES)


def registered_workflow(name: ExecutableWorkflowName) -> RegisteredWorkflow:
    return REGISTRY_NAMES[name]
