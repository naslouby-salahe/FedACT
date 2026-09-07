from __future__ import annotations

from pathlib import Path

from tests.architecture.architecture_rules import (
    module_name,
    parse_source,
    production_source_files,
)


def test_every_production_python_file_is_inspected_by_the_architecture_scanner(
    repository_root: Path,
) -> None:
    discovered = {
        source_file.resolve() for source_file in (repository_root / "src" / "fedact").rglob("*.py")
    }
    scanned = {source_file.resolve() for source_file in production_source_files(repository_root)}
    assert scanned, "architecture scanner discovered no production source files"
    missing = discovered - scanned
    assert not missing, (
        "production source files not inspected by the architecture scanner:\n"
        + "\n".join(sorted(str(path) for path in missing))
    )
    for source_file in scanned:
        assert source_file.is_file()
        parse_source(source_file)
        assert module_name(repository_root, source_file)


def test_scanner_coverage_rejects_a_new_untracked_source_file(tmp_path: Path) -> None:
    package = tmp_path / "src" / "fedact"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (package / "visible.py").write_text("def visible() -> None:\n    return\n", encoding="utf-8")
    (package / "also_visible.py").write_text(
        "def also_visible() -> None:\n    return\n", encoding="utf-8"
    )
    discovered = {
        source_file.resolve() for source_file in (tmp_path / "src" / "fedact").rglob("*.py")
    }
    scanned = {source_file.resolve() for source_file in production_source_files(tmp_path)}
    assert discovered - scanned == set()
