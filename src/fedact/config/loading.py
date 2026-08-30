from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import NewType, Self, cast

import yaml

from fedact.config.models import FedActConfig
from fedact.config.validation import validate_configuration_constraints
from fedact.domain.types import JsonEncodableValue

ConfigurationHash = NewType("ConfigurationHash", str)
ConfigurationPayloadText = NewType("ConfigurationPayloadText", str)


class DuplicateYamlKeyError(ValueError):
    pass


class _DuplicateKeyRejectingLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: yaml.Loader, node: yaml.Node) -> dict[object, object]:
    if not isinstance(node, yaml.MappingNode):
        raise TypeError("configuration mappings must deserialize from YAML mapping nodes")
    seen: set[object] = set()
    for key_node, _unused in node.value:
        key = cast(object, loader.construct_object(key_node))
        if key in seen:
            raise DuplicateYamlKeyError(f"duplicate configuration key encountered: {key!r}")
        seen.add(key)
    return cast(dict[object, object], loader.construct_mapping(node))


_DuplicateKeyRejectingLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


def deterministic_configuration_payload(config: FedActConfig) -> ConfigurationPayloadText:
    return ConfigurationPayloadText(
        json.dumps(
            config.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        )
    )


def compute_configuration_hash(config: FedActConfig) -> ConfigurationHash:
    digest = hashlib.sha256(deterministic_configuration_payload(config).encode("utf-8"))
    return ConfigurationHash(f"sha256:{digest.hexdigest()}")


def parse_configuration_payload(payload: ConfigurationPayloadText) -> FedActConfig:
    raw = yaml.load(payload, Loader=_DuplicateKeyRejectingLoader)
    if not isinstance(raw, dict):
        raise ValueError("configuration payload must deserialize to a mapping")
    return FedActConfig.model_validate(cast(dict[str, object], raw))


@dataclass(frozen=True)
class LoadedConfiguration:
    path: Path
    values: FedActConfig
    hash: ConfigurationHash

    @classmethod
    def from_payload(cls, path: Path, payload: ConfigurationPayloadText) -> Self:
        values = parse_configuration_payload(payload)
        validate_configuration_constraints(values)
        return cls(path=path, values=values, hash=compute_configuration_hash(values))


def parse_raw_configuration_mapping(payload: ConfigurationPayloadText) -> JsonEncodableValue:
    raw = yaml.load(payload, Loader=_DuplicateKeyRejectingLoader)
    if not isinstance(raw, dict):
        raise ValueError("configuration payload must deserialize to a mapping")
    return cast(JsonEncodableValue, raw)


def _deep_merge(base: JsonEncodableValue, overlay: JsonEncodableValue) -> JsonEncodableValue:
    if not isinstance(base, dict) or not isinstance(overlay, dict):
        return overlay
    merged: dict[str, JsonEncodableValue] = dict(base)
    for key, value in overlay.items():
        merged[key] = _deep_merge(merged[key], value) if key in merged else value
    return merged


def load_overlay_configuration(overlay_file: Path, production_file: Path) -> LoadedConfiguration:
    overlay_values = parse_raw_configuration_mapping(
        ConfigurationPayloadText(overlay_file.read_text(encoding="utf-8"))
    )
    production_values = parse_raw_configuration_mapping(
        ConfigurationPayloadText(production_file.read_text(encoding="utf-8"))
    )
    merged = _deep_merge(production_values, overlay_values)
    values = FedActConfig.model_validate(merged)
    validate_configuration_constraints(values)
    return LoadedConfiguration(
        path=overlay_file.resolve(),
        values=values,
        hash=compute_configuration_hash(values),
    )


def load_production_configuration(configuration_file: Path) -> LoadedConfiguration:
    payload = ConfigurationPayloadText(configuration_file.read_text(encoding="utf-8"))
    return LoadedConfiguration.from_payload(configuration_file.resolve(), payload)
