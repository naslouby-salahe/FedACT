from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.architecture_rules import (
    function_parameter_annotations,
    module_name,
    parse_source,
    production_source_files,
    relative_source_path,
)

CONFIGURATION_OWNER_PREFIXES = ("fedact.config",)
CONTEXT_OWNER_MODULES = frozenset({"fedact.app"})
FORBIDDEN_CONFIG_TYPES = frozenset(
    {
        "FedActConfig",
        "StatisticsConfig",
        "HardeningConfig",
        "TrainingConfig",
        "IdentificationConfig",
        "CertificationConfig",
        "TemporalConfig",
        "SyntheticConfig",
        "LoadedConfiguration",
    }
)


def config_parameter_violations_for_tree(module: str, path: str, tree: ast.Module) -> list[str]:
    if module.startswith(CONFIGURATION_OWNER_PREFIXES) or module in CONTEXT_OWNER_MODULES:
        return []
    violations: list[str] = []
    for function_name, lineno, argument, names in function_parameter_annotations(tree):
        leaked = sorted(names & FORBIDDEN_CONFIG_TYPES)
        if leaked:
            violations.append(
                f"{path}:{lineno}: {function_name} parameter {argument} threads {leaked}"
            )
    return violations


def config_parameter_violations(repository_root: Path) -> list[str]:
    violations: list[str] = []
    for source_file in production_source_files(repository_root):
        module = module_name(repository_root, source_file)
        path = relative_source_path(repository_root, source_file)
        violations.extend(
            config_parameter_violations_for_tree(module, path, parse_source(source_file))
        )
    return violations


def test_configuration_is_not_passed_through_ordinary_service_parameters(
    repository_root: Path,
) -> None:
    violations = config_parameter_violations(repository_root)
    assert not violations, "configuration parameter threading:\n" + "\n".join(violations)


def test_config_threading_rule_detects_service_config_parameters() -> None:
    tree = ast.parse("def run(config: FedActConfig) -> None:\n    return\n")
    violations = config_parameter_violations_for_tree(
        "fedact.experiments.prospective", "x.py", tree
    )
    assert violations


def test_config_threading_rule_accepts_application_context_owner() -> None:
    tree = ast.parse(
        "def from_repository_root(cls, configuration: LoadedConfiguration) -> object:\n"
        "    return cls\n"
    )
    assert config_parameter_violations_for_tree("fedact.app", "src/fedact/app.py", tree) == []
