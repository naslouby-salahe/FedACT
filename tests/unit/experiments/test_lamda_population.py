from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from fedact.config.loading import LoadedConfiguration
from fedact.experiments.lamda_population import eligible_cutoffs, load_lamda_population
from fedact.workflow import Application

PRODUCTION_CONFIGURATION = Path(__file__).resolve().parents[3] / "configs" / "fedact.yaml"
LAMDA_RELEASE_DIRECTORY = "data/raw/LAMDA/Baseline"
FEATURE_COLUMN_COUNT = 2
DISCARDED_VT_COUNT = 2


def _application_without_corpus(
    tmp_path: Path, production_configuration: LoadedConfiguration
) -> Application:
    (tmp_path / "configs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "fedact"\n', encoding="utf-8")
    shutil.copy(PRODUCTION_CONFIGURATION, tmp_path / "configs" / "fedact.yaml")
    return Application(repository_root=tmp_path, configuration=production_configuration)


def _write_non_auditable_release(repository_root: Path) -> None:
    release_directory = repository_root / LAMDA_RELEASE_DIRECTORY
    release_directory.mkdir(parents=True, exist_ok=True)
    rows = []
    for index in range(8):
        row: dict[str, object] = {
            "hash": hashlib.sha256(f"discarded-{index}".encode()).hexdigest(),
            "year_month": "2023-01",
            "label": None,
            "vt_count": DISCARDED_VT_COUNT,
            "family": "berbew",
        }
        for column in range(FEATURE_COLUMN_COUNT):
            row[f"feat_{column}"] = float(index + column) / 8.0
        rows.append(row)
    pd.DataFrame(rows).to_parquet(release_directory / "lamda_baseline.parquet", index=False)


def test_population_is_absent_when_the_release_directory_is_missing(
    tmp_path: Path, production_configuration: LoadedConfiguration
) -> None:
    application = _application_without_corpus(tmp_path, production_configuration)
    assert load_lamda_population(application) is None


def test_population_is_absent_when_no_row_carries_an_auditable_label(
    tmp_path: Path, production_configuration: LoadedConfiguration
) -> None:
    application = _application_without_corpus(tmp_path, production_configuration)
    _write_non_auditable_release(application.repository_root)
    assert load_lamda_population(application) is None


def test_population_aligns_features_labels_months_and_identities(
    lamda_corpus_application: Application,
) -> None:
    population = load_lamda_population(lamda_corpus_application)
    assert population is not None
    row_count = population.features.shape[0]
    assert row_count == population.labels.shape[0] == population.months.shape[0]
    assert row_count == len(population.sample_ids) == len(population.family)
    assert population.labels.dtype == np.bool_
    assert all(sample_id for sample_id in population.sample_ids)
    assert len(set(population.sample_ids)) == row_count
    assert set(np.unique(population.labels)) == {False, True}


def test_eligible_cutoffs_require_support_in_both_windows(
    lamda_corpus_application: Application,
) -> None:
    population = load_lamda_population(lamda_corpus_application)
    assert population is not None
    cutoffs = eligible_cutoffs(lamda_corpus_application, population)
    assert cutoffs
    lowest = int(population.months.min())
    highest = int(population.months.max())
    assert all(lowest <= cutoff <= highest for cutoff in cutoffs)
    assert list(cutoffs) == sorted(cutoffs)


def test_eligible_cutoffs_is_empty_for_a_population_without_history(
    lamda_corpus_application: Application,
) -> None:
    population = load_lamda_population(lamda_corpus_application)
    assert population is not None
    single_month = type(population)(
        features=population.features,
        labels=population.labels,
        months=np.zeros_like(population.months),
        sample_ids=population.sample_ids,
        family=population.family,
    )
    assert eligible_cutoffs(lamda_corpus_application, single_month) == ()
