from __future__ import annotations

import ast
from pathlib import Path

BANNED_FAIL_OPEN_IDENTIFIERS = frozenset(
    {
        "DEFAULT_ALLOWED",
        "DICT_BOUNDARY_ALLOWED_FILES",
        "FUNCTION_ALLOWLIST",
        "OBJECT_BOUNDARY_ALLOWED_FILES",
        "PACKAGE_PRIMITIVE_ALLOWLIST",
        "PRIMITIVE_KEYED_DICT_PATTERN",
        "REGISTERED_PRODUCTION_MODULES",
        "SILENT_EXCEPT_PATTERN",
    }
)
NEGATIVE_CANARY_TOKENS = frozenset({"bypass", "detect", "escape", "reject"})
POSITIVE_CANARY_TOKENS = frozenset({"accept", "clean", "complete", "does_not", "ignore", "private", "valid"})
SELF_FILE = "test_architecture_suite_self_integrity.py"


def assignment_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def string_literals(node: ast.AST) -> list[str]:
    return [
        child.value
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    ]


def detector_helpers(tree: ast.Module) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    return [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and "violation" in node.name
        and not node.name.startswith("test_")
    ]


def test_function_names(tree: ast.Module) -> set[str]:
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    }


def has_token(name: str, tokens: frozenset[str]) -> bool:
    return any(token in name for token in tokens)


def manual_module_registry_violations(path: str, tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        literals = string_literals(node)
        python_paths = [value for value in literals if value.endswith(".py")]
        if len(python_paths) >= 8:
            violations.append(
                f"{path}: manual production-module registry contains {len(python_paths)} Python paths"
            )
    return violations


def broad_exception_policy_violations(path: str, tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for name in assignment_names(tree):
        upper = name.upper()
        if "ALLOWLIST" in upper:
            violations.append(f"{path}: architecture rule declares allowlist {name}")
        if "PACKAGE" in upper and "EXEMPT" in upper:
            violations.append(f"{path}: architecture rule declares package-wide exemption {name}")
    return violations


def detector_canary_violations(path: str, tree: ast.Module) -> list[str]:
    if not detector_helpers(tree):
        return []
    names = test_function_names(tree)
    violations: list[str] = []
    if not any(has_token(name, NEGATIVE_CANARY_TOKENS) for name in names):
        violations.append(f"{path}: detector has no adversarial rejection/detection canary")
    if not any(has_token(name, POSITIVE_CANARY_TOKENS) for name in names):
        violations.append(f"{path}: detector has no valid positive counterexample canary")
    return violations


def architecture_self_integrity_violations(repository_root: Path) -> list[str]:
    architecture_root = repository_root / "tests" / "architecture"
    violations: list[str] = []
    for source_file in sorted(architecture_root.glob("*.py")):
        if source_file.name in {"__init__.py", "architecture_rules.py", SELF_FILE}:
            continue
        relative = source_file.relative_to(repository_root).as_posix()
        text = source_file.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(source_file))
        names = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
        for forbidden in sorted(BANNED_FAIL_OPEN_IDENTIFIERS & names):
            violations.append(f"{relative}: reintroduces banned fail-open identifier {forbidden}")
        violations.extend(manual_module_registry_violations(relative, tree))
        violations.extend(broad_exception_policy_violations(relative, tree))
        violations.extend(detector_canary_violations(relative, tree))
    return violations


def test_architecture_tests_are_fail_closed_and_self_testing(repository_root: Path) -> None:
    violations = architecture_self_integrity_violations(repository_root)
    assert not violations, "architecture-suite self-integrity violations:\n" + "\n".join(violations)


def test_self_integrity_detector_rejects_fail_open_patterns(tmp_path: Path) -> None:
    architecture_root = tmp_path / "tests" / "architecture"
    architecture_root.mkdir(parents=True)
    bad = architecture_root / "test_bad_rule.py"
    bad.write_text(
        "DEFAULT_ALLOWED = frozenset({'fedact.domain'})\n"
        "PACKAGE_ALLOWLIST = {'fedact.domain'}\n"
        "def boundary_violations():\n    return []\n"
        "def test_rule_rejects_bad_case():\n    assert True\n",
        encoding="utf-8",
    )
    assert architecture_self_integrity_violations(tmp_path)


def test_self_integrity_detector_accepts_fail_closed_detector(tmp_path: Path) -> None:
    architecture_root = tmp_path / "tests" / "architecture"
    architecture_root.mkdir(parents=True)
    good = architecture_root / "test_good_rule.py"
    good.write_text(
        "def boundary_violations():\n    return []\n"
        "def test_rule_rejects_bad_case():\n    assert True\n"
        "def test_rule_accepts_good_case():\n    assert True\n",
        encoding="utf-8",
    )
    assert architecture_self_integrity_violations(tmp_path) == []
