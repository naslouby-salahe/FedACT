from __future__ import annotations

from fedact.domain.enums import ExecutableWorkflowName
from fedact.experiments.definitions import (
    REGISTRY_NAMES,
    WORKFLOW_REGISTRY,
    registered_workflow,
)


def test_registry_contains_every_executable_workflow() -> None:
    assert {workflow.name for workflow in WORKFLOW_REGISTRY} == set(ExecutableWorkflowName)


def test_every_dependency_names_a_known_executable_workflow() -> None:
    known = set(ExecutableWorkflowName)
    for workflow in WORKFLOW_REGISTRY:
        assert set(workflow.required_dependencies) <= known


def test_dependency_graph_is_acyclic() -> None:
    visited: dict[ExecutableWorkflowName, bool] = {}

    def visit(name: ExecutableWorkflowName, stack: frozenset[ExecutableWorkflowName]) -> None:
        if name in stack:
            raise AssertionError(f"dependency cycle at {name}")
        if visited.get(name):
            return
        for dependency in REGISTRY_NAMES[name].required_dependencies:
            if dependency in REGISTRY_NAMES:
                visit(dependency, stack | {name})
        visited[name] = True

    for workflow_name in REGISTRY_NAMES:
        visit(workflow_name, frozenset())


def test_only_client_selection_is_optional_in_the_cli_registry() -> None:
    optional = {workflow.name for workflow in WORKFLOW_REGISTRY if workflow.optional}
    assert optional == {ExecutableWorkflowName.CLIENT_SELECTION}


def test_statistical_synthesis_does_not_depend_on_client_selection() -> None:
    synthesis = registered_workflow(ExecutableWorkflowName.STATISTICAL_SYNTHESIS)
    assert ExecutableWorkflowName.CLIENT_SELECTION not in synthesis.required_dependencies


def test_smoke_is_a_prerequisite_of_synthetic_geometry() -> None:
    geometry = registered_workflow(ExecutableWorkflowName.SYNTHETIC_GEOMETRY)
    assert ExecutableWorkflowName.SMOKE in geometry.required_dependencies
    assert ExecutableWorkflowName.SMOKE in REGISTRY_NAMES
