from __future__ import annotations

import ast
import io
import tokenize
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

BARE_PRIMITIVES = frozenset({"str", "int", "float", "bool", "bytes"})
ANY_NAMES = frozenset({"Any"})
OBJECT_NAMES = frozenset({"object"})
MAPPING_NAMES = frozenset({"dict", "Dict", "Mapping", "MutableMapping"})
SEMANTIC_WRAPPERS = frozenset({"Annotated"})
BOUNDARY_BASES = frozenset({"BaseModel", "TypedDict", "NamedTuple", "Protocol"})
FORBIDDEN_DYNAMIC_CALLS = frozenset({"eval", "exec", "compile"})
SAFE_NUMERIC_LITERALS = frozenset({0, 1, -1})


@dataclass(frozen=True)
class AnnotationSite:
    module: str
    symbol: str
    kind: str
    lineno: int
    annotation: ast.expr


@dataclass(frozen=True)
class ImportEdge:
    importer: str
    imported: str
    lineno: int


@dataclass(frozen=True)
class NumericLiteralSite:
    path: str
    symbol: str
    kind: str
    lineno: int
    value: int | float


def production_source_files(repository_root: Path) -> list[Path]:
    return sorted((repository_root / "src" / "fedact").rglob("*.py"))


def relative_source_path(repository_root: Path, source_file: Path) -> str:
    return source_file.relative_to(repository_root).as_posix()


def module_name(repository_root: Path, source_file: Path) -> str:
    relative = source_file.relative_to(repository_root / "src").with_suffix("")
    module = ".".join(relative.parts)
    if module.endswith(".__init__"):
        return module[: -len(".__init__")]
    return module


def parse_source(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def terminal_name(node: ast.expr | ast.AST | None) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def qualified_name(node: ast.expr | ast.AST | None) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = qualified_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return None


def collect_type_aliases(tree: ast.Module) -> dict[str, ast.expr]:
    aliases: dict[str, ast.expr] = {}
    for node in tree.body:
        if isinstance(node, ast.TypeAlias):
            aliases[node.name.id] = node.value
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id[:1].isupper():
                aliases[target.id] = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value:
            if node.target.id[:1].isupper():
                aliases[node.target.id] = node.value
        elif isinstance(node, ast.ImportFrom) and node.module == "builtins":
            for imported in node.names:
                if imported.name in BARE_PRIMITIVES:
                    aliases[imported.asname or imported.name] = ast.Name(id=imported.name)
    return aliases


def _is_semantic_alias_expression(node: ast.expr) -> bool:
    if isinstance(node, ast.Call) and terminal_name(node.func) == "NewType":
        return True
    return isinstance(node, ast.Subscript) and terminal_name(node.value) in SEMANTIC_WRAPPERS


def primitive_names(
    annotation: ast.expr | None,
    aliases: dict[str, ast.expr],
    resolving: frozenset[str] = frozenset(),
) -> set[str]:
    if annotation is None:
        return set()
    if isinstance(annotation, ast.Name):
        if annotation.id in BARE_PRIMITIVES:
            return {annotation.id}
        target = aliases.get(annotation.id)
        if target is None or annotation.id in resolving or _is_semantic_alias_expression(target):
            return set()
        return primitive_names(target, aliases, resolving | {annotation.id})
    if isinstance(annotation, ast.Attribute):
        full = qualified_name(annotation)
        if full and full.startswith("builtins.") and annotation.attr in BARE_PRIMITIVES:
            return {annotation.attr}
        return set()
    if isinstance(annotation, ast.Subscript):
        if terminal_name(annotation.value) in SEMANTIC_WRAPPERS:
            return set()
        return primitive_names(annotation.value, aliases, resolving) | primitive_names(
            annotation.slice, aliases, resolving
        )
    if isinstance(annotation, ast.BinOp):
        return primitive_names(annotation.left, aliases, resolving) | primitive_names(
            annotation.right, aliases, resolving
        )
    if isinstance(annotation, ast.Tuple):
        found: set[str] = set()
        for element in annotation.elts:
            found |= primitive_names(element, aliases, resolving)
        return found
    if isinstance(annotation, ast.Call):
        if terminal_name(annotation.func) == "NewType":
            return set()
        found = primitive_names(annotation.func, aliases, resolving)
        for argument in annotation.args:
            found |= primitive_names(argument, aliases, resolving)
        return found
    return set()


def annotation_contains_names(annotation: ast.expr, names: frozenset[str]) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(annotation):
        if isinstance(node, ast.Name) and node.id in names:
            found.add(node.id)
        elif isinstance(node, ast.Attribute) and node.attr in names:
            found.add(node.attr)
    return found


def annotation_mapping_names(annotation: ast.expr) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(annotation):
        if isinstance(node, (ast.Name, ast.Attribute)):
            name = terminal_name(node)
            if name in MAPPING_NAMES:
                found.add(name)
    return found


def is_record_boundary_class(node: ast.ClassDef) -> bool:
    decorator_names = {terminal_name(decorator) for decorator in node.decorator_list}
    base_names = {terminal_name(base) for base in node.bases}
    return "dataclass" in decorator_names or bool(base_names & BOUNDARY_BASES)


def is_typer_command_function(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Attribute) and target.attr == "command":
            return True
    return False


def _iter_function_sites(
    module: str,
    prefix: str,
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> Iterator[AnnotationSite]:
    if node.name.startswith("_"):
        return
    symbol = f"{prefix}.{node.name}" if prefix else f"{module}.{node.name}"
    is_cli_command = is_typer_command_function(node)
    positional = [*node.args.posonlyargs, *node.args.args]
    if positional and positional[0].arg in {"self", "cls"}:
        positional = positional[1:]
    if not is_cli_command:
        for argument in [*positional, *node.args.kwonlyargs]:
            if argument.annotation is not None:
                yield AnnotationSite(
                    module=module,
                    symbol=symbol,
                    kind=f"parameter:{argument.arg}",
                    lineno=argument.lineno,
                    annotation=argument.annotation,
                )
        if node.args.vararg and node.args.vararg.annotation is not None:
            yield AnnotationSite(
                module=module,
                symbol=symbol,
                kind=f"vararg:{node.args.vararg.arg}",
                lineno=node.args.vararg.lineno,
                annotation=node.args.vararg.annotation,
            )
        if node.args.kwarg and node.args.kwarg.annotation is not None:
            yield AnnotationSite(
                module=module,
                symbol=symbol,
                kind=f"kwarg:{node.args.kwarg.arg}",
                lineno=node.args.kwarg.lineno,
                annotation=node.args.kwarg.annotation,
            )
    if node.returns is not None:
        yield AnnotationSite(
            module=module,
            symbol=symbol,
            kind="return",
            lineno=node.lineno,
            annotation=node.returns,
        )


def annotation_sites(module: str, tree: ast.Module) -> list[AnnotationSite]:
    sites: list[AnnotationSite] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            sites.extend(_iter_function_sites(module, "", node))
        elif isinstance(node, ast.ClassDef):
            class_symbol = f"{module}.{node.name}"
            if is_record_boundary_class(node):
                for item in node.body:
                    if (
                        isinstance(item, ast.AnnAssign)
                        and isinstance(item.target, ast.Name)
                        and not item.target.id.startswith("_")
                    ):
                        sites.append(
                            AnnotationSite(
                                module=module,
                                symbol=class_symbol,
                                kind=f"field:{item.target.id}",
                                lineno=item.lineno,
                                annotation=item.annotation,
                            )
                        )
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    sites.extend(_iter_function_sites(module, class_symbol, item))
    return sites


def missing_public_annotations(module: str, tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in tree.body:
        candidates: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            candidates.append((module, node))
        elif isinstance(node, ast.ClassDef):
            candidates.extend(
                (f"{module}.{node.name}", item)
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
        for prefix, function in candidates:
            if function.name.startswith("_"):
                continue
            symbol = f"{prefix}.{function.name}"
            positional = [*function.args.posonlyargs, *function.args.args]
            if positional and positional[0].arg in {"self", "cls"}:
                positional = positional[1:]
            arguments = [*positional, *function.args.kwonlyargs]
            if function.args.vararg:
                arguments.append(function.args.vararg)
            if function.args.kwarg:
                arguments.append(function.args.kwarg)
            for argument in arguments:
                if argument.annotation is None:
                    violations.append(
                        f"{symbol}:{argument.lineno}: unannotated parameter {argument.arg}"
                    )
            if function.returns is None:
                violations.append(f"{symbol}:{function.lineno}: missing return annotation")
    return violations


def resolve_relative_import(importer: str, level: int, imported: str | None) -> str:
    package_parts = importer.split(".")[:-1]
    ascend = max(level - 1, 0)
    if ascend > len(package_parts):
        return ""
    base = package_parts[: len(package_parts) - ascend] if ascend else package_parts
    if imported:
        base.extend(imported.split("."))
    return ".".join(base)


def import_edges(importer: str, tree: ast.Module) -> list[ImportEdge]:
    edges: list[ImportEdge] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for imported in node.names:
                if imported.name == "fedact" or imported.name.startswith("fedact."):
                    edges.append(ImportEdge(importer, imported.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                resolved = resolve_relative_import(importer, node.level, node.module)
                if resolved:
                    edges.append(ImportEdge(importer, resolved, node.lineno))
            elif node.module and (node.module == "fedact" or node.module.startswith("fedact.")):
                if node.module == "fedact":
                    for imported in node.names:
                        if imported.name != "*":
                            edges.append(
                                ImportEdge(importer, f"fedact.{imported.name}", node.lineno)
                            )
                else:
                    edges.append(ImportEdge(importer, node.module, node.lineno))
    return edges


def silent_exception_sites(path: str, tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        meaningful = [
            statement
            for statement in node.body
            if not (
                isinstance(statement, ast.Expr)
                and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)
            )
        ]
        if not meaningful or all(isinstance(statement, ast.Pass) for statement in meaningful):
            violations.append(f"{path}:{node.lineno}: silently swallowed exception")
    return violations


def forbidden_dynamic_call_sites(path: str, tree: ast.Module) -> list[str]:
    violations: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in FORBIDDEN_DYNAMIC_CALLS
        ):
            violations.append(f"{path}:{node.lineno}: forbidden {node.func.id}()")
    return violations


def suppression_comment_sites(path: str, text: str) -> list[str]:
    violations: list[str] = []
    tokens = tokenize.generate_tokens(io.StringIO(text).readline)
    for token in tokens:
        if token.type != tokenize.COMMENT:
            continue
        lowered = token.string.lower()
        if "type: ignore" in lowered or "noqa" in lowered or "pyright: ignore" in lowered:
            violations.append(f"{path}:{token.start[0]}: static-analysis suppression")
    return violations


def _enclosing_symbol(parents: dict[ast.AST, ast.AST], node: ast.AST) -> str:
    current = node
    while current in parents:
        current = parents[current]
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
        if isinstance(current, ast.ClassDef):
            return current.name
    return "<module>"


def numeric_literal_sites(path: str, tree: ast.Module) -> list[NumericLiteralSite]:
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    sites: list[NumericLiteralSite] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant):
            continue
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            continue
        value: int | float = node.value
        parent = parents.get(node)
        if isinstance(parent, ast.UnaryOp) and isinstance(parent.op, ast.USub):
            value = -value
        kind = type(parent).__name__ if parent is not None else "Constant"
        sites.append(
            NumericLiteralSite(
                path=path,
                symbol=_enclosing_symbol(parents, node),
                kind=kind,
                lineno=node.lineno,
                value=value,
            )
        )
    return sites


def numeric_defaults(tree: ast.Module) -> list[tuple[str, int, int | float]]:
    violations: list[tuple[str, int, int | float]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        positional_names = [argument.arg for argument in [*node.args.posonlyargs, *node.args.args]]
        defaults = list(node.args.defaults)
        positional_defaults = positional_names[len(positional_names) - len(defaults) :]
        for name, default in zip(positional_defaults, defaults, strict=True):
            value = _numeric_value(default)
            if value is not None and value not in SAFE_NUMERIC_LITERALS:
                violations.append((f"{node.name}:{name}", default.lineno, value))
        for argument, default in zip(node.args.kwonlyargs, node.args.kw_defaults, strict=True):
            if default is None:
                continue
            value = _numeric_value(default)
            if value is not None and value not in SAFE_NUMERIC_LITERALS:
                violations.append((f"{node.name}:{argument.arg}", default.lineno, value))
    return violations


def governed_keyword_literals(
    tree: ast.Module, governed: frozenset[str]
) -> list[tuple[str, int, str]]:
    violations: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg is None:
                continue
            value = _numeric_value(keyword.value)
            if value is None:
                continue
            rendered = repr(value)
            if rendered in governed:
                violations.append((keyword.arg, keyword.value.lineno, rendered))
    return violations


def governed_collection_literals(
    tree: ast.Module, governed: frozenset[str]
) -> list[tuple[int, str]]:
    violations: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            continue
        for element in node.elts:
            value = _numeric_value(element)
            if value is not None and repr(value) in governed:
                violations.append((element.lineno, repr(value)))
    return violations


def _numeric_value(node: ast.AST) -> int | float | None:
    if (
        isinstance(node, ast.Constant)
        and not isinstance(node.value, bool)
        and isinstance(node.value, (int, float))
    ):
        return node.value
    if (
        isinstance(node, ast.UnaryOp)
        and isinstance(node.op, ast.USub)
        and isinstance(node.operand, ast.Constant)
        and not isinstance(node.operand.value, bool)
        and isinstance(node.operand.value, (int, float))
    ):
        return -node.operand.value
    return None


def enum_definitions(tree: ast.Module) -> dict[str, frozenset[str]]:
    definitions: dict[str, frozenset[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        if not any(terminal_name(base) in {"Enum", "StrEnum", "IntEnum"} for base in node.bases):
            continue
        values: set[str] = set()
        for item in node.body:
            if (
                isinstance(item, ast.Assign)
                and len(item.targets) == 1
                and isinstance(item.targets[0], ast.Name)
                and isinstance(item.value, ast.Constant)
                and isinstance(item.value.value, str)
            ):
                values.add(item.value.value)
        definitions[node.name] = frozenset(values)
    return definitions


def string_literal_sites(tree: ast.Module) -> Iterator[ast.Constant]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node
