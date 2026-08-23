from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from fedact.config.loading import (
    DuplicateYamlKeyError,
    LoadedConfiguration,
    canonical_configuration_payload,
    compute_configuration_hash,
    load_production_configuration,
    parse_configuration_payload,
)
from fedact.config.models import FedActConfig


def test_production_configuration_loads_with_expected_hash_format(
    production_configuration_path: Path,
) -> None:
    loaded = load_production_configuration(production_configuration_path)
    digest = loaded.hash.removeprefix("sha256:")
    assert len(digest) == 64
    int(digest, 16)
    assert loaded.path == production_configuration_path.resolve()


def test_configuration_hash_is_deterministic_across_loads(
    production_configuration: LoadedConfiguration,
    production_configuration_path: Path,
) -> None:
    reloaded = load_production_configuration(production_configuration_path)
    assert reloaded.hash == production_configuration.hash
    assert compute_configuration_hash(reloaded.values) == production_configuration.hash


def test_every_value_change_changes_the_configuration_hash(production_payload: str) -> None:
    baseline = FedActConfig.model_validate(yaml.safe_load(production_payload))
    mutated_payload = production_payload.replace("1001, 1002", "1011, 1002", 1)
    assert mutated_payload != production_payload
    mutated = FedActConfig.model_validate(yaml.safe_load(mutated_payload))

    assert compute_configuration_hash(baseline) != compute_configuration_hash(mutated)


def test_canonical_payload_round_trips_through_parsing_without_drift(
    production_configuration: LoadedConfiguration,
) -> None:
    payload = canonical_configuration_payload(production_configuration.values)
    reparsed = parse_configuration_payload(payload)
    assert reparsed == production_configuration.values
    assert canonical_configuration_payload(reparsed) == payload
    assert ": " not in payload


def test_duplicate_yaml_keys_are_rejected() -> None:
    duplicated = "training:\n  batch_size: 256\n  batch_size: 128\n"
    with pytest.raises(DuplicateYamlKeyError):
        parse_configuration_payload(duplicated)


def test_non_mapping_payloads_are_rejected() -> None:
    with pytest.raises((ValueError, ValidationError)):
        parse_configuration_payload("- 1\n- 2\n")
