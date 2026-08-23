from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml


def collect_scalar_leaves(node: object) -> list[object]:
    if isinstance(node, dict):
        mapping = cast(dict[object, object], node)
        return [leaf for child in mapping.values() for leaf in collect_scalar_leaves(child)]
    if isinstance(node, list):
        items = cast(list[object], node)
        return [leaf for child in items for leaf in collect_scalar_leaves(child)]
    return [node]


def test_committed_configuration_matches_roadmap_block(
    roadmap_configuration_block: str, production_payload: str
) -> None:
    assert production_payload == roadmap_configuration_block


def test_no_parallel_configuration_file_duplicates_production_values(
    repository_root: Path, production_payload: str
) -> None:
    authoritative_raw = cast(dict[object, object], yaml.safe_load(production_payload))
    governed_scalars = {
        repr(leaf)
        for leaf in collect_scalar_leaves(authoritative_raw)
        if not isinstance(leaf, bool)
    }

    scanned: list[Path] = []
    configs_root = repository_root / "configs"
    scanned.extend(sorted(p for p in configs_root.glob("*") if p.suffix in {".yaml", ".yml"}))
    docs_root = repository_root / "docs"
    if docs_root.is_dir():
        scanned.extend(sorted(docs_root.rglob("*.yml")))

    duplications: list[str] = []
    for candidate in scanned:
        if candidate == configs_root / "fedact.yaml":
            continue
        loaded = yaml.safe_load(candidate.read_text(encoding="utf-8"))
        if loaded is None:
            continue
        assert isinstance(loaded, dict), f"{candidate} must deserialize to a mapping"
        raw = cast(dict[object, object], loaded)
        duplicated = {repr(leaf) for leaf in collect_scalar_leaves(raw)} & governed_scalars
        if duplicated:
            duplications.append(
                f"{candidate.relative_to(repository_root)} duplicates {sorted(duplicated)}"
            )

    assert not duplications, f"parallel configuration duplication detected: {duplications}"
