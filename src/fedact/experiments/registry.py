from __future__ import annotations

from dataclasses import dataclass

from fedact.domain.enums import ExecutableWorkflowName
from fedact.domain.types import OptionalFlag, RoadmapSectionId, WorkflowDescription


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
    wf.name: wf for wf in WORKFLOW_REGISTRY
}


def registered_workflow(name: ExecutableWorkflowName) -> RegisteredWorkflow:
    if name in REGISTRY_NAMES:
        return REGISTRY_NAMES[name]
    raise KeyError(f"Workflow {name.value} not registered in scientific registry")


def registered_workflow_for(workflow_name: ExecutableWorkflowName) -> RegisteredWorkflow:
    return registered_workflow(workflow_name)


CLI_SELECTABLE_WORKFLOWS: tuple[ExecutableWorkflowName, ...] = tuple(
    wf.name for wf in WORKFLOW_REGISTRY
)
