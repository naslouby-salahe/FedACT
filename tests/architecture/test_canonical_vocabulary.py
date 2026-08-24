from __future__ import annotations

import ast
import re
from pathlib import Path

FORBIDDEN_PREDECESSOR_ALIASES: frozenset[str] = frozenset(
    {
        "fedsira",
        "fabrid",
        "datp",
        "trajcert",
        "fedorbit",
        "fedcampaign",
        "fed_sira",
        "fab_rid",
        "dat_p",
        "traj_cert",
        "fed_orbit",
        "fed_campaign",
    }
)

FORBIDDEN_GENERIC_NAMES: frozenset[str] = frozenset(
    {
        "utils",
        "util",
        "helpers",
        "helper",
        "common",
        "manager",
        "processor",
        "misc",
        "stuff",
        "do_it",
        "run_all",
    }
)

ARTIFICIAL_VERSION_PATTERN = re.compile(
    r"(^|_)((v|ver|version)[0-9]+|final[0-9]*|legacy|compat|draft)($|_)",
    re.IGNORECASE,
)

MACHINE_STYLE_EXPERIMENT_PATTERN = re.compile(
    r"(^|_)(exp|experiment|run|trial)[0-9]+($|_)",
    re.IGNORECASE,
)

TOKEN_SPLIT_PATTERN = re.compile(r"[_\s\-]+|(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])")


def tokenize_identifier(name: str) -> list[str]:
    return [token.lower() for token in TOKEN_SPLIT_PATTERN.split(name) if token]


class VocabularyAstVisitor(ast.NodeVisitor):
    def __init__(self, relative_path: str) -> None:
        self.relative_path = relative_path
        self.violations: list[str] = []

    def _check_name(self, name: str, node_type: str, lineno: int) -> None:
        tokens = set(tokenize_identifier(name))
        lower_name = name.lower()

        for forbidden in FORBIDDEN_PREDECESSOR_ALIASES:
            if forbidden in lower_name or forbidden in tokens:
                self.violations.append(
                    f"{self.relative_path}:{lineno}: {node_type} '{name}' contains forbidden alias '{forbidden}'"
                )

        if ARTIFICIAL_VERSION_PATTERN.search(name):
            self.violations.append(
                f"{self.relative_path}:{lineno}: {node_type} '{name}' uses artificial version naming"
            )

        if lower_name in FORBIDDEN_GENERIC_NAMES or any(t in FORBIDDEN_GENERIC_NAMES for t in tokens):
            self.violations.append(
                f"{self.relative_path}:{lineno}: {node_type} '{name}' uses forbidden generic terminology"
            )

        if MACHINE_STYLE_EXPERIMENT_PATTERN.search(name):
            self.violations.append(
                f"{self.relative_path}:{lineno}: {node_type} '{name}' uses machine-style/numbered naming"
            )

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._check_name(node.name, "class", node.lineno)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if not (node.name.startswith("__") and node.name.endswith("__")):
            self._check_name(node.name, "function/method", node.lineno)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        if not (node.name.startswith("__") and node.name.endswith("__")):
            self._check_name(node.name, "async function/method", node.lineno)
        self.generic_visit(node)

    def visit_arg(self, node: ast.arg) -> None:
        if node.arg not in {"self", "cls"}:
            self._check_name(node.arg, "parameter", node.lineno)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Store):
            self._check_name(node.id, "variable", node.lineno)
        self.generic_visit(node)

    def visit_alias(self, node: ast.alias) -> None:
        if node.asname:
            self._check_name(node.asname, "import alias", 1)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant) -> None:
        if isinstance(node.value, str):
            lower_val = node.value.lower()
            for forbidden in FORBIDDEN_PREDECESSOR_ALIASES:
                if forbidden in lower_val:
                    self.violations.append(
                        f"{self.relative_path}:{node.lineno}: string literal '{node.value}' contains forbidden alias '{forbidden}'"
                    )
        self.generic_visit(node)


def source_vocabulary_violations(repository_root: Path) -> list[str]:
    roots: list[Path] = [repository_root / "src", repository_root / "tests"]
    violations: list[str] = []
    for root in roots:
        for source_file in sorted(root.rglob("*.py")):
            if source_file.name == "test_canonical_vocabulary.py":
                continue
            relative = source_file.relative_to(repository_root).as_posix()
            lower_stem = source_file.stem.lower()
            for forbidden in FORBIDDEN_PREDECESSOR_ALIASES:
                if forbidden in lower_stem:
                    violations.append(
                        f"{relative}: file name contains forbidden alias '{forbidden}'"
                    )
            if ARTIFICIAL_VERSION_PATTERN.search(source_file.stem):
                violations.append(
                    f"{relative}: file name uses artificial version naming"
                )
            if lower_stem in FORBIDDEN_GENERIC_NAMES:
                violations.append(
                    f"{relative}: file name uses forbidden generic terminology"
                )
            try:
                tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
            except SyntaxError as parse_error:
                violations.append(f"{relative}:{parse_error.lineno}: syntax error {parse_error.msg}")
                continue
            visitor = VocabularyAstVisitor(relative)
            visitor.visit(tree)
            violations.extend(visitor.violations)
    return violations


def configuration_vocabulary_violations(repository_root: Path) -> list[str]:
    configs_root = repository_root / "configs"
    violations: list[str] = []
    if not configs_root.exists():
        return violations
    for config_file in sorted(configs_root.rglob("*")):
        if config_file.suffix not in {".yaml", ".yml"}:
            continue
        relative = config_file.relative_to(repository_root).as_posix()
        for line_number, line in enumerate(
            config_file.read_text(encoding="utf-8").splitlines(), start=1
        ):
            lower_line = line.lower()
            for forbidden in FORBIDDEN_PREDECESSOR_ALIASES:
                if forbidden in lower_line:
                    violations.append(
                        f"{relative}:{line_number}: configuration line contains forbidden alias '{forbidden}'"
                    )
    return violations


def test_sources_use_only_canonical_fedact_vocabulary(repository_root: Path) -> None:
    violations = source_vocabulary_violations(repository_root)
    assert not violations, f"stale non-FedACT vocabulary found in sources: {violations}"


def test_configurations_use_only_canonical_fedact_vocabulary(repository_root: Path) -> None:
    violations = configuration_vocabulary_violations(repository_root)
    assert not violations, f"stale non-FedACT vocabulary found in configuration: {violations}"


def test_ast_visitor_detects_forbidden_predecessors_and_artificial_versions() -> None:
    snippet = """
class FedSiraModel_v2:
    def execute_datp_run(self, old_param: int) -> None:
        fabrid_metric = old_param + 1
        exp1 = "some_value"
"""
    tree = ast.parse(snippet)
    visitor = VocabularyAstVisitor("test_snippet.py")
    visitor.visit(tree)
    assert len(visitor.violations) >= 4
    joined = " ".join(visitor.violations)
    assert "fedsira" in joined
    assert "datp" in joined
    assert "old_param" in joined
    assert "fabrid" in joined
