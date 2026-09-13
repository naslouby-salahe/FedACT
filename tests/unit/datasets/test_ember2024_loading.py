from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from fedact.data.ember2024 import (
    LoadedEmberDataset,
    load_ember2024_records,
    run_empty_ember_transform_audit,
    validate_ember_dataset,
)

SUBMISSION_EPOCH_SECONDS = 1672531200
SAMPLE_HASH_A = "a" * 64
SAMPLE_HASH_B = "b" * 64
POPULATED_FEATURE_DIMENSION = 2613
DOS_HEADER_MEMBERS = (
    "e_magic",
    "e_cblp",
    "e_cp",
    "e_crlc",
    "e_cparhdr",
    "e_minalloc",
    "e_maxalloc",
    "e_ss",
    "e_sp",
    "e_csum",
    "e_ip",
    "e_cs",
    "e_lfarlc",
    "e_ovno",
    "e_oemid",
    "e_oeminfo",
    "e_lfanew",
)


def ember_record(*, label: int, sample_hash: str, family: str) -> dict[str, object]:
    return {
        "sha256": sample_hash,
        "label": label,
        "first_submission_date": SUBMISSION_EPOCH_SECONDS,
        "family": family,
        "general": {
            "size": 4096,
            "start_bytes": [77, 90, 144, 0, 3, 0, 0, 0],
            "is_pe": 1,
            "entropy": 6.5,
        },
        "histogram": [0] * 256,
        "byteentropy": [0] * 256,
        "strings": {
            "numstrings": 10,
            "avlength": 5.0,
            "printables": 100,
            "printabledist": [0] * 96,
            "entropy": 4.0,
            "string_counts": {},
        },
        "header": {
            "coff": {
                "timestamp": 0,
                "machine": "",
                "number_of_sections": 1,
                "number_of_symbols": 0,
                "pointer_to_symbol_table": 0,
                "characteristics": [],
                "sizeof_optional_header": 224,
            },
            "optional": {
                "major_linker_version": 0,
                "minor_linker_version": 0,
                "sizeof_code": 512,
                "sizeof_initialized_data": 0,
                "sizeof_uninitialized_data": 0,
                "address_of_entrypoint": 4096,
                "base_of_code": 4096,
                "image_base": 4194304,
                "section_alignment": 4096,
                "checksum": 0,
                "subsystem": "",
                "dll_characteristics": [],
                "sizeof_stack_reserve": 0,
                "sizeof_stack_commit": 0,
                "sizeof_heap_reserve": 0,
                "sizeof_heap_commit": 0,
                "number_of_rvas_and_sizes": 16,
                "major_operating_system_version": 6,
                "minor_operating_system_version": 0,
                "major_image_version": 0,
                "minor_image_version": 0,
                "major_subsystem_version": 6,
                "minor_subsystem_version": 0,
                "sizeof_image": 8192,
                "sizeof_headers": 1024,
            },
            "dos": {member: 0 for member in DOS_HEADER_MEMBERS},
        },
        "section": {
            "sections": [
                {
                    "name": ".text",
                    "size": 512,
                    "vsize": 600,
                    "entropy": 6.0,
                    "props": ["CNT_CODE"],
                    "size_ratio": 0.1,
                    "vsize_ratio": 0.1,
                    "entry": ".text",
                    "overlay": {},
                }
            ],
            "overlay": {},
        },
        "imports": {"kernel32.dll": ["GetProcAddress"]},
        "exports": ["Exported"],
        "datadirectories": [
            {"has_relocs": 1, "has_dynamic_relocs": 0},
            {"name": "EXPORT", "size": 1, "virtual_address": 2},
            {"name": "IMPORT", "size": 3, "virtual_address": 4},
        ],
        "richheader": [1, 2, 3, 4],
        "authenticode": {
            "num_certs": 1,
            "self_signed": 0,
            "empty_program_name": 0,
            "no_countersigner": 0,
            "parse_error": 0,
            "chain_max_depth": 1,
            "latest_signing_time": 0,
            "signing_time_diff": 0,
        },
        "pefilewarnings": ["warning"],
    }


def _write_jsonl(
    directory: Path, records: list[dict[str, object]], *, blanks: bool = False
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    destination = directory / "ember2024.jsonl"
    lines = [json.dumps(record) for record in records]
    if blanks:
        lines.insert(0, "")
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return destination


def test_records_and_features_load_from_jsonl(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path,
        [
            ember_record(label=1, sample_hash=SAMPLE_HASH_A, family="berbew"),
            ember_record(label=0, sample_hash=SAMPLE_HASH_B, family="drixed"),
        ],
    )
    loaded = load_ember2024_records(tmp_path)
    assert len(loaded.records) == 2
    assert loaded.features.shape == (2, POPULATED_FEATURE_DIMENSION)
    assert loaded.records[0].sample_hash == SAMPLE_HASH_A
    assert loaded.records[0].label is True
    assert loaded.records[1].label is False
    assert loaded.records[1].family == "drixed"
    assert loaded.records[0].year_month == "2023-01"


def test_blank_lines_are_skipped(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path,
        [ember_record(label=1, sample_hash=SAMPLE_HASH_A, family="berbew")],
        blanks=True,
    )
    assert len(load_ember2024_records(tmp_path).records) == 1


def test_unlabelled_records_keep_no_binary_label(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path,
        [ember_record(label=-1, sample_hash=SAMPLE_HASH_A, family="berbew")],
    )
    assert load_ember2024_records(tmp_path).records[0].label is None


def test_a_directory_without_jsonl_files_yields_an_empty_dataset(tmp_path: Path) -> None:
    loaded = load_ember2024_records(tmp_path)
    assert loaded.records == ()
    assert loaded.features.shape[0] == 0


def test_validate_ember_dataset_accepts_a_loaded_dataset(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path,
        [ember_record(label=1, sample_hash=SAMPLE_HASH_A, family="berbew")],
    )
    validate_ember_dataset(load_ember2024_records(tmp_path))


def test_validate_ember_dataset_rejects_mismatched_rows(tmp_path: Path) -> None:
    loaded = load_ember2024_records(tmp_path)
    mismatched = LoadedEmberDataset(
        records=loaded.records, features=np.zeros((1, POPULATED_FEATURE_DIMENSION))
    )
    with pytest.raises(ValueError, match="record count and feature rows must match"):
        validate_ember_dataset(mismatched)


def test_empty_ember_transform_audit_runs_without_evidence() -> None:
    run_empty_ember_transform_audit()
