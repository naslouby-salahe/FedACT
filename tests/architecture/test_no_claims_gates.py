from __future__ import annotations

import ast
from pathlib import Path

from tests.architecture.architecture_rules import (
    parse_source,
    production_source_files,
    relative_source_path,
)

FORBIDDEN_CLAIM_GATE_IDENTIFIERS = frozenset(
    {
        "Claim",
        "ClaimState",
        "ClaimGate",
        "ClaimResult",
        "ClaimRegistry",
        "ClaimEvaluator",
        "ClaimManifest",
        "GateResult",
        "primary_claim_confirmed",
        "claim_state",
    }
)


def claims_gates_violations_for_tree(path: str, tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_CLAIM_GATE_IDENTIFIERS:
            violations.append(f"{path}:{node.lineno}: forbidden claims/gates identifier {node.id}")
        elif isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_CLAIM_GATE_IDENTIFIERS:
            violations.append(f"{path}:{node.lineno}: forbidden claims/gates attribute {node.attr}")
        elif isinstance(node, ast.ClassDef) and node.name in FORBIDDEN_CLAIM_GATE_IDENTIFIERS:
            violations.append(f"{path}:{node.lineno}: forbidden claims/gates class {node.name}")
        elif (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name in FORBIDDEN_CLAIM_GATE_IDENTIFIERS
        ):
            violations.append(f"{path}:{node.lineno}: forbidden claims/gates function {node.name}")
        elif isinstance(node, ast.alias):
            identifier = node.asname or node.name.rsplit(".", 1)[-1]
            if identifier in FORBIDDEN_CLAIM_GATE_IDENTIFIERS:
                violations.append(
                    f"{path}:1: forbidden claims/gates import {node.name}"
                    + (f" as {node.asname}" if node.asname else "")
                )
    return violations


def claims_gates_violations(repository_root: Path) -> list[str]:
    violations: list[str] = []
    for source_file in production_source_files(repository_root):
        path = relative_source_path(repository_root, source_file)
        violations.extend(claims_gates_violations_for_tree(path, parse_source(source_file)))
    return violations


def test_production_code_does_not_use_manuscript_claims_or_gates(
    repository_root: Path,
) -> None:
    violations = claims_gates_violations(repository_root)
    assert not violations, "claims/gates vocabulary in production:\n" + "\n".join(violations)


def test_claims_gates_rule_detects_forbidden_identifiers() -> None:
    tree = ast.parse(
        "class ClaimState:\n    pass\n"
        "def mark(primary_claim_confirmed: bool) -> None:\n"
        "    claim_state = ClaimState()\n"
    )
    violations = claims_gates_violations_for_tree("example.py", tree)
    assert violations


def test_claims_gates_rule_accepts_measurement_status_vocabulary() -> None:
    tree = ast.parse(
        "class EvidenceStatus:\n    SUPPORTED = 'SUPPORTED'\n"
        "def evaluate_contrast() -> EvidenceStatus:\n"
        "    return EvidenceStatus.SUPPORTED\n"
    )
    assert claims_gates_violations_for_tree("example.py", tree) == []
