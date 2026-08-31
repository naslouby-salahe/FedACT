from __future__ import annotations

from pathlib import Path
from typing import cast

import yaml

from fedact.config.loading import load_overlay_configuration, load_production_configuration


def collect_key_paths(node: object, prefix: str = "") -> set[str]:
    if isinstance(node, dict):
        mapping = cast(dict[object, object], node)
        keys: set[str] = set()
        for key, value in mapping.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            keys.add(path)
            keys |= collect_key_paths(value, path)
        return keys
    return set()


def test_overlay_configurations_are_partial_fragments_of_the_authoritative_schema(
    repository_root: Path,
) -> None:
    configs_root = repository_root / "configs"
    overlays = sorted(
        candidate for candidate in configs_root.glob("*.y*ml") if candidate.name != "fedact.yaml"
    )
    assert overlays, "overlay configuration discovery must be non-empty"

    loaded_authoritative = yaml.safe_load(
        (configs_root / "fedact.yaml").read_text(encoding="utf-8")
    )
    assert isinstance(loaded_authoritative, dict)
    authoritative_paths = collect_key_paths(cast(dict[object, object], loaded_authoritative))

    for overlay in overlays:
        loaded_overlay = yaml.safe_load(overlay.read_text(encoding="utf-8"))
        assert isinstance(loaded_overlay, dict), f"{overlay.name} must deserialize to a mapping"
        overlay_values = cast(dict[object, object], loaded_overlay)
        for path in collect_key_paths(overlay_values):
            assert path in authoritative_paths, (
                f"{overlay.name} introduces unknown schema path {path}"
            )
        merged = load_overlay_configuration(overlay, configs_root / "fedact.yaml")
        production = load_production_configuration(configs_root / "fedact.yaml")
        assert merged.hash != production.hash or not overlay_values, (
            f"{overlay.name} must change the resolved configuration"
        )
