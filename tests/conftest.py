from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pytest
import yaml

from fedact.app import Application
from fedact.config.loading import LoadedConfiguration, load_production_configuration

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PRODUCTION_CONFIGURATION_PATH = REPOSITORY_ROOT / "configs" / "fedact.yaml"
SOURCE_ROOT = REPOSITORY_ROOT / "src"
TESTS_ROOT = REPOSITORY_ROOT / "tests"


@pytest.fixture(scope="session")
def repository_root() -> Path:
    return REPOSITORY_ROOT


@pytest.fixture(scope="session")
def production_configuration_path() -> Path:
    return PRODUCTION_CONFIGURATION_PATH


@pytest.fixture(scope="session")
def production_configuration() -> LoadedConfiguration:
    return load_production_configuration(PRODUCTION_CONFIGURATION_PATH)


@pytest.fixture(scope="session")
def application(
    repository_root: Path, production_configuration: LoadedConfiguration
) -> Application:
    return Application(repository_root=repository_root, configuration=production_configuration)


@pytest.fixture(scope="session")
def production_payload() -> str:
    return PRODUCTION_CONFIGURATION_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def governed_scalar_literals(production_payload: str) -> frozenset[str]:
    raw = cast(dict[object, object], yaml.safe_load(production_payload))

    def collect_leaves(node: object) -> Iterator[float | int]:
        if isinstance(node, bool):
            return
        if isinstance(node, (int, float)):
            yield node
            return
        if isinstance(node, dict):
            mapping = cast(dict[object, object], node)
            for child in mapping.values():
                yield from collect_leaves(child)
            return
        if isinstance(node, list):
            for child in cast(list[object], node):
                yield from collect_leaves(child)

    return frozenset(
        repr(value) for value in collect_leaves(raw) if repr(value) not in {"0", "0.0", "1", "1.0"}
    )
