from __future__ import annotations

import hashlib
import shutil
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest

from fedact.config.loading import LoadedConfiguration
from fedact.workflow import Application

PRODUCTION_CONFIGURATION = Path(__file__).resolve().parents[3] / "configs" / "fedact.yaml"
LAMDA_RELEASE_DIRECTORY = "data/raw/LAMDA/Baseline"
DOMINANT_FAMILY = "berbew"
SECONDARY_FAMILIES = ("drixed", "other")
CHRONOLOGY_MONTHS = (
    "2023-01",
    "2023-02",
    "2023-03",
    "2023-04",
    "2023-05",
    "2023-06",
    "2023-07",
    "2023-08",
    "2023-09",
    "2023-10",
)
SAMPLES_PER_CLASS_PER_MONTH = 120
SECONDARY_FAMILY_SAMPLES = 40
FEATURE_COLUMN_COUNT = 4
MALICIOUS_VT_COUNT = 9
BENIGN_VT_COUNT = 0


def _feature_value(sample_index: int, column: int, malicious: bool) -> float:
    return float((sample_index + column) % 11) / 11.0 + (0.5 if malicious else 0.0)


def build_lamda_corpus(repository_root: Path) -> Path:
    release_directory = repository_root / LAMDA_RELEASE_DIRECTORY
    release_directory.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    sample_index = 0
    for year_month in CHRONOLOGY_MONTHS:
        for malicious in (True, False):
            for _ in range(SAMPLES_PER_CLASS_PER_MONTH):
                row: dict[str, object] = {
                    "hash": hashlib.sha256(
                        f"{year_month}-{DOMINANT_FAMILY}-{malicious}-{sample_index}".encode()
                    ).hexdigest(),
                    "year_month": year_month,
                    "label": malicious,
                    "vt_count": MALICIOUS_VT_COUNT if malicious else BENIGN_VT_COUNT,
                    "family": DOMINANT_FAMILY,
                }
                for column in range(FEATURE_COLUMN_COUNT):
                    row[f"feat_{column}"] = _feature_value(sample_index, column, malicious)
                rows.append(row)
                sample_index += 1
    for family in SECONDARY_FAMILIES:
        for _ in range(SECONDARY_FAMILY_SAMPLES):
            row = {
                "hash": hashlib.sha256(f"{family}-{sample_index}".encode()).hexdigest(),
                "year_month": CHRONOLOGY_MONTHS[len(CHRONOLOGY_MONTHS) // 2],
                "label": True,
                "vt_count": MALICIOUS_VT_COUNT,
                "family": family,
            }
            for column in range(FEATURE_COLUMN_COUNT):
                row[f"feat_{column}"] = _feature_value(sample_index, column, True)
            rows.append(row)
            sample_index += 1
    pd.DataFrame(rows).to_parquet(release_directory / "lamda_baseline.parquet", index=False)
    return release_directory


@pytest.fixture(scope="module")
def lamda_corpus_application(
    tmp_path_factory: pytest.TempPathFactory,
    production_configuration: LoadedConfiguration,
) -> Iterator[Application]:
    repository_root = tmp_path_factory.mktemp("lamda-corpus")
    (repository_root / "configs").mkdir(parents=True, exist_ok=True)
    (repository_root / "pyproject.toml").write_text(
        '[project]\nname = "fedact"\n', encoding="utf-8"
    )
    shutil.copy(PRODUCTION_CONFIGURATION, repository_root / "configs" / "fedact.yaml")
    build_lamda_corpus(repository_root)
    yield Application(repository_root=repository_root, configuration=production_configuration)
