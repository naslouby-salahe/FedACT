from __future__ import annotations

import ast
from pathlib import Path

BARE_PRIMITIVES: frozenset[str] = frozenset({"str", "int", "float", "bool", "bytes"})
PACKAGE_PRIMITIVE_ALLOWLIST: dict[str, frozenset[str]] = {
    "fedact.config": frozenset({"str", "int", "float", "bool"}),
    "fedact.cli": frozenset({"bool", "str"}),
}
FUNCTION_ALLOWLIST: dict[str, frozenset[str]] = {}


def _matching_allowlist_package(module_path: str) -> str:
    matches = [
        package for package in PACKAGE_PRIMITIVE_ALLOWLIST if module_path.startswith(package + ".")
    ]
    return max(matches, key=len) if matches else module_path.rsplit(".", 1)[0]


def public_function_boundaries(
    tree: ast.AST,
) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    boundaries: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            boundaries.append((node.name, node))
    return boundaries


def annotation_primitives(annotation: ast.expr | None) -> set[str]:
    if annotation is None:
        return set()
    rendered = ast.unparse(annotation)
    parts = {fragment.strip("[] |,") for fragment in rendered.replace("|", "[").split("[")}
    return {primitive for primitive in parts if primitive in BARE_PRIMITIVES}


def primitive_leak_violations(repository_root: Path) -> list[str]:
    package_root = repository_root / "src"
    violations: list[str] = []
    for source_file in sorted(package_root.rglob("*.py")):
        relative = source_file.relative_to(repository_root / "src").with_suffix("")
        module_path = str(relative).replace("/", ".")
        if module_path.endswith(".__init__"):
            module_path = module_path[: -len(".__init__")]
        owning_package = _matching_allowlist_package(module_path)
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for function_name, node in public_function_boundaries(tree):
            qualified = f"{module_path}.{function_name}"
            allowed_primitives = PACKAGE_PRIMITIVE_ALLOWLIST.get(
                owning_package, frozenset()
            ) | FUNCTION_ALLOWLIST.get(qualified, frozenset())
            arguments = [*node.args.args, *node.args.kwonlyargs]
            if arguments and arguments[0].arg == "self":
                arguments = arguments[1:]
            for argument in arguments:
                leaked = annotation_primitives(argument.annotation) - allowed_primitives
                if leaked:
                    violations.append(
                        f"{relative.as_posix()}:{node.lineno}: {function_name} parameter "
                        f"{argument.arg}: {sorted(leaked)}"
                    )
            returned: set[str] = set()
            if node.returns is not None:
                is_predicate = function_name.startswith(("is_", "has_", "should_"))
                is_bool_return = ast.unparse(node.returns) == "bool"
                if not (is_predicate and is_bool_return):
                    returned = annotation_primitives(node.returns)
                returned -= allowed_primitives
            if returned:
                violations.append(
                    f"{relative.as_posix()}:{node.lineno}: {function_name} return: "
                    f"{sorted(returned)}"
                )
    return violations


def test_public_functions_do_not_leak_bare_primitives(repository_root: Path) -> None:
    violations = primitive_leak_violations(repository_root)
    assert not violations, f"primitive leakage across public boundaries: {violations}"


def test_allowlists_reference_real_targets(repository_root: Path) -> None:
    for package in PACKAGE_PRIMITIVE_ALLOWLIST:
        assert (repository_root / "src" / package.replace(".", "/")).is_dir()
    for qualified in FUNCTION_ALLOWLIST:
        module_path, function_name = qualified.rsplit(".", 1)
        source_file = repository_root / "src" / (module_path.replace(".", "/") + ".py")
        assert source_file.is_file(), f"stale function allowlist: {qualified}"
        tree = ast.parse(source_file.read_text(encoding="utf-8"))
        names = {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
        assert function_name in names, f"stale function allowlist: {qualified}"


def dataclass_primitive_violations(repository_root: Path) -> list[str]:
    package_root = repository_root / "src"
    violations: list[str] = []
    for source_file in sorted(package_root.rglob("*.py")):
        relative = source_file.relative_to(repository_root / "src").with_suffix("")
        module_path = str(relative).replace("/", ".")
        if "fedact.config" in module_path:
            continue
        owning_package = _matching_allowlist_package(module_path)
        allowed_primitives = PACKAGE_PRIMITIVE_ALLOWLIST.get(owning_package, frozenset())
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                is_dc = any(
                    (isinstance(d, ast.Name) and d.id == "dataclass")
                    or (
                        isinstance(d, ast.Call)
                        and isinstance(d.func, ast.Name)
                        and d.func.id == "dataclass"
                    )
                    for d in node.decorator_list
                )
                if is_dc:
                    for item in node.body:
                        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                            field_name = item.target.id
                            is_predicate = field_name.startswith(
                                ("is_", "has_", "should_")
                            ) or field_name.endswith(
                                (
                                    "_passed",
                                    "_supported",
                                    "_valid",
                                    "_flag",
                                    "_present",
                                    "_ok",
                                    "_recorded",
                                    "_validate",
                                    "_verified",
                                    "_confirmed",
                                    "_characterized",
                                    "_satisfied",
                                    "_committed",
                                    "_only",
                                    "_name",
                                )
                            )
                            leaked = annotation_primitives(item.annotation) - allowed_primitives
                            if is_predicate and leaked == {"bool"}:
                                continue
                            if field_name.endswith("_name") and leaked == {"str"}:
                                continue
                            if leaked:
                                loc = f"{relative.as_posix()}:{item.lineno}"
                                violations.append(
                                    f"{loc}: {node.name}.{field_name}: {sorted(leaked)}"
                                )
    return violations


def test_dataclasses_do_not_leak_bare_primitives(repository_root: Path) -> None:
    violations = dataclass_primitive_violations(repository_root)
    assert not violations, f"primitive leakage in dataclass fields: {violations}"
