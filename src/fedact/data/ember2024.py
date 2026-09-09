from __future__ import annotations

import json
import math
import shutil
import struct
import subprocess
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import NewType, cast

import lief
import numpy as np
from sklearn.feature_extraction import FeatureHasher

from fedact.data.records import ClientSemanticsAudit
from fedact.domain.types import (
    BinaryLabel,
    CalendarMonthString,
    ClientSemanticsClass,
    ConfirmatoryFormat,
    DatasetSelector,
    DegeneracyFlag,
    DetailMessage,
    DisplacementComponent,
    EpochSeconds,
    FamilyName,
    JsonEncodableValue,
    NormValue,
    SampleCount,
    SampleIdentifier,
    SupportThreshold,
    ValidationFlag,
    ZeroDisplacementFloor,
)

_STRING_PRINTABLE_BIN_COUNT = 96
_SECTION_HASH_BUCKETS = 50
_SECTION_CHARACTERISTICS_HASH_BUCKETS = 50
_SECTION_ENTRY_NAME_HASH_BUCKETS = 10
_IMPORT_LIBRARY_HASH_BUCKETS = 256
_IMPORT_FUNCTION_HASH_BUCKETS = 1024
_EXPORT_HASH_BUCKETS = 128
_RICH_HEADER_HASH_BUCKETS = 32
_DATA_DIRECTORY_COUNT = 16
_AUTHENTICODE_DIMENSION = 8
_HEADER_DIMENSION = 74
_HEADER_VERSION_FIELD_COUNT = 8
_HEADER_SIZEOF_FIELD_COUNT = 9
_SECTION_HASH_GROUP_TOTAL = 3
_PAIRED_ENTRY_WIDTH = 2
_IMPORT_SUMMARY_FIELD_COUNT = 2

_PEFILE_WARNINGS_PATH = Path(__file__).parent / "pefile_warnings.txt"

_STRING_REGEX_NAMES = (
    ".click(",
    "/EmbeddedFile",
    "/FlateDecode",
    "/URI",
    "/bin/",
    "/dev/",
    "/proc/",
    "/tmp/",
    "/usr/",
    "<script",
    "Invoke-Command",
    "Invoke-Expression",
    "Start-process",
    "base64",
    "base64string",
    "btc_wallet",
    "cache",
    "certificate",
    "clipboard",
    "command",
    "connect",
    "cookie",
    "create",
    "crypt",
    "debug",
    "decode",
    "delete",
    "desktop",
    "directory",
    "disk",
    "dos_msg",
    "download",
    "email_addr",
    "encode",
    "enum",
    "environment",
    "exit",
    "file",
    "file_path",
    "ftp",
    "get",
    "hidden",
    "hostname",
    "html",
    "http",
    "http://",
    "https://",
    "install",
    "internet",
    "ipv4_addr",
    "ipv6_addr",
    "javascript",
    "keyboard",
    "mac_addr",
    "memory",
    "module",
    "mutex",
    "onlick",
    "password",
    "post",
    "powershell",
    "privilege",
    "process",
    "registry_key",
    "remote",
    "resource",
    "security",
    "service",
    "shell",
    "snapshot",
    "system",
    "thread",
    "token",
    "url",
    "useragent",
    "wallet",
    "window",
)
_STRING_REGEX_INDEX = {name: index for index, name in enumerate(_STRING_REGEX_NAMES)}

_MACHINE_TYPES = (
    "IMAGE_FILE_MACHINE_UNKNOWN",
    "IMAGE_FILE_MACHINE_I386",
    "IMAGE_FILE_MACHINE_R3000",
    "IMAGE_FILE_MACHINE_R4000",
    "IMAGE_FILE_MACHINE_R10000",
    "IMAGE_FILE_MACHINE_WCEMIPSV2",
    "IMAGE_FILE_MACHINE_ALPHA",
    "IMAGE_FILE_MACHINE_SH3",
    "IMAGE_FILE_MACHINE_SH3DSP",
    "IMAGE_FILE_MACHINE_SH3E",
    "IMAGE_FILE_MACHINE_SH4",
    "IMAGE_FILE_MACHINE_SH5",
    "IMAGE_FILE_MACHINE_ARM",
    "IMAGE_FILE_MACHINE_THUMB",
    "IMAGE_FILE_MACHINE_ARMNT",
    "IMAGE_FILE_MACHINE_AM33",
    "IMAGE_FILE_MACHINE_POWERPC",
    "IMAGE_FILE_MACHINE_POWERPCFP",
    "IMAGE_FILE_MACHINE_IA64",
    "IMAGE_FILE_MACHINE_MIPS16",
    "IMAGE_FILE_MACHINE_ALPHA64",
    "IMAGE_FILE_MACHINE_AXP64",
    "IMAGE_FILE_MACHINE_MIPSFPU",
    "IMAGE_FILE_MACHINE_MIPSFPU16",
    "IMAGE_FILE_MACHINE_TRICORE",
    "IMAGE_FILE_MACHINE_CEF",
    "IMAGE_FILE_MACHINE_EBC",
    "IMAGE_FILE_MACHINE_RISCV32",
    "IMAGE_FILE_MACHINE_RISCV64",
    "IMAGE_FILE_MACHINE_RISCV128",
    "IMAGE_FILE_MACHINE_LOONGARCH32",
    "IMAGE_FILE_MACHINE_LOONGARCH64",
    "IMAGE_FILE_MACHINE_AMD64",
    "IMAGE_FILE_MACHINE_M32R",
    "IMAGE_FILE_MACHINE_ARM64",
    "IMAGE_FILE_MACHINE_CEE",
)
_MACHINE_TYPE_INDEX = {name: index for index, name in enumerate(_MACHINE_TYPES)}

_SUBSYSTEM_TYPES = (
    "IMAGE_SUBSYSTEM_UNKNOWN",
    "IMAGE_SUBSYSTEM_NATIVE",
    "IMAGE_SUBSYSTEM_WINDOWS_GUI",
    "IMAGE_SUBSYSTEM_WINDOWS_CUI",
    "IMAGE_SUBSYSTEM_OS2_CUI",
    "IMAGE_SUBSYSTEM_POSIX_CUI",
    "IMAGE_SUBSYSTEM_NATIVE_WINDOWS",
    "IMAGE_SUBSYSTEM_WINDOWS_CE_GUI",
    "IMAGE_SUBSYSTEM_EFI_APPLICATION",
    "IMAGE_SUBSYSTEM_EFI_BOOT_SERVICE_DRIVER",
    "IMAGE_SUBSYSTEM_EFI_RUNTIME_DRIVER",
    "IMAGE_SUBSYSTEM_EFI_ROM",
    "IMAGE_SUBSYSTEM_XBOX",
    "IMAGE_SUBSYSTEM_WINDOWS_BOOT_APPLICATION",
)
_SUBSYSTEM_TYPE_INDEX = {name: index for index, name in enumerate(_SUBSYSTEM_TYPES)}

_IMAGE_CHARACTERISTICS = (
    "RELOCS_STRIPPED",
    "EXECUTABLE_IMAGE",
    "LINE_NUMS_STRIPPED",
    "LOCAL_SYMS_STRIPPED",
    "AGGRESIVE_WS_TRIM",
    "LARGE_ADDRESS_AWARE",
    "16BIT_MACHINE",
    "BYTES_REVERSED_LO",
    "32BIT_MACHINE",
    "DEBUG_STRIPPED",
    "REMOVABLE_RUN_FROM_SWAP",
    "NET_RUN_FROM_SWAP",
    "SYSTEM",
    "DLL",
    "UP_SYSTEM_ONLY",
    "BYTES_REVERSED_HI",
)
_DLL_CHARACTERISTICS = (
    "HIGH_ENTROPY_VA",
    "DYNAMIC_BASE",
    "FORCE_INTEGRITY",
    "NX_COMPAT",
    "NO_ISOLATION",
    "NO_SEH",
    "NO_BIND",
    "APPCONTAINER",
    "WDM_DRIVER",
    "GUARD_CF",
    "TERMINAL_SERVER_AWARE",
)
_DOS_HEADER_MEMBERS = (
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
_DATA_DIRECTORY_NAMES = (
    "EXPORT",
    "IMPORT",
    "RESOURCE",
    "EXCEPTION",
    "SECURITY",
    "BASERELOC",
    "DEBUG",
    "COPYRIGHT",
    "GLOBALPTR",
    "TLS",
    "LOAD_CONFIG",
    "BOUND_IMPORT",
    "IAT",
    "DELAY_IMPORT",
    "COM_DESCRIPTOR",
    "RESERVED",
)


def _pefile_warning_index() -> dict[str, int]:
    lines = [
        line for line in _PEFILE_WARNINGS_PATH.read_text(encoding="utf-8").splitlines() if line
    ]
    return {line: index for index, line in enumerate(lines)}


_PEFILE_WARNING_INDEX = _pefile_warning_index()
_PEFILE_WARNING_DIMENSION = len(_PEFILE_WARNING_INDEX) + 1


_FEATURE_HASHER_TRANSFORM_ATTRIBUTE = "transform"
_SPARSE_MATRIX_TO_ARRAY_ATTRIBUTE = "toarray"

EmberJsonObject = NewType("EmberJsonObject", dict[str, JsonEncodableValue])
EmberJsonObjectList = NewType("EmberJsonObjectList", list[EmberJsonObject])
EmberJsonStringList = NewType("EmberJsonStringList", list[str])
EmberJsonIntegerList = NewType("EmberJsonIntegerList", list[int])


def _scalar(value: JsonEncodableValue) -> float:
    if isinstance(value, (int, float)):
        return float(value)
    raise TypeError(f"EMBER numeric feature has unsupported value {value!r}")


def _hashed_row(hasher: FeatureHasher, values: Sequence[JsonEncodableValue]) -> np.ndarray:
    dense = cast(np.ndarray, hasher.transform([list(values)]).toarray())
    return dense[0]


def _general_file_info_vector(general: EmberJsonObject) -> np.ndarray:
    start_bytes = cast(EmberJsonIntegerList, general["start_bytes"])
    return np.array(
        [
            _scalar(general["size"]),
            _scalar(general["entropy"]),
            _scalar(general["is_pe"]),
            *[float(value) for value in start_bytes],
        ],
        dtype=np.float32,
    )


def _general_file_info_count_mask() -> np.ndarray:
    return np.array([True, False, False, False, False, False, False])


def _normalized_histogram_vector(histogram: EmberJsonIntegerList) -> np.ndarray:
    counts = np.array(histogram, dtype=np.float32)
    total = counts.sum()
    return counts / total if total > 0 else counts


def _string_extractor_vector(strings: EmberJsonObject) -> np.ndarray:
    printables = _scalar(strings["printables"])
    divisor = float(printables) if printables > 0 else 1.0
    string_counts = np.zeros(len(_STRING_REGEX_NAMES), dtype=np.float32)
    string_counts_payload = cast(EmberJsonObject, strings["string_counts"])
    for regex_name, count in string_counts_payload.items():
        string_counts[_STRING_REGEX_INDEX[regex_name]] = _scalar(count)
    printable_distribution = np.asarray(strings["printabledist"], dtype=np.float32) / divisor
    return np.hstack(
        [
            _scalar(strings["numstrings"]),
            _scalar(strings["avlength"]),
            float(printables),
            printable_distribution,
            _scalar(strings["entropy"]),
            string_counts,
        ]
    ).astype(np.float32)


def _string_extractor_count_mask() -> np.ndarray:
    return np.hstack(
        [
            [True, False, True],
            np.zeros(_STRING_PRINTABLE_BIN_COUNT, dtype=bool),
            [False],
            np.ones(len(_STRING_REGEX_NAMES), dtype=bool),
        ]
    )


def _header_file_info_vector(header: EmberJsonObject) -> np.ndarray:
    if not header:
        return np.zeros(_HEADER_DIMENSION, dtype=np.float32)
    coff = cast(EmberJsonObject, header["coff"])
    optional = cast(EmberJsonObject, header["optional"])
    dos = cast(EmberJsonObject, header["dos"])
    machine_index = _MACHINE_TYPE_INDEX.get(cast(str, coff["machine"]), 0)
    subsystem_index = _SUBSYSTEM_TYPE_INDEX.get(cast(str, optional["subsystem"]), 0)
    coff_characteristics = cast(EmberJsonStringList, coff["characteristics"])
    dll_characteristics = cast(EmberJsonStringList, optional["dll_characteristics"])
    image_flags = [1.0 if flag in coff_characteristics else 0.0 for flag in _IMAGE_CHARACTERISTICS]
    dll_flags = [1.0 if flag in dll_characteristics else 0.0 for flag in _DLL_CHARACTERISTICS]
    dos_values = [_scalar(dos[member]) for member in _DOS_HEADER_MEMBERS]
    return np.hstack(
        [
            _scalar(coff["timestamp"]),
            _scalar(coff["number_of_sections"]),
            _scalar(coff["number_of_symbols"]),
            _scalar(coff["sizeof_optional_header"]),
            _scalar(coff["pointer_to_symbol_table"]),
            float(machine_index),
            float(subsystem_index),
            _scalar(optional["major_image_version"]),
            _scalar(optional["minor_image_version"]),
            _scalar(optional["major_linker_version"]),
            _scalar(optional["minor_linker_version"]),
            _scalar(optional["major_operating_system_version"]),
            _scalar(optional["minor_operating_system_version"]),
            _scalar(optional["major_subsystem_version"]),
            _scalar(optional["minor_subsystem_version"]),
            _scalar(optional["sizeof_code"]),
            _scalar(optional["sizeof_headers"]),
            _scalar(optional["sizeof_image"]),
            _scalar(optional["sizeof_initialized_data"]),
            _scalar(optional["sizeof_uninitialized_data"]),
            _scalar(optional["sizeof_stack_reserve"]),
            _scalar(optional["sizeof_stack_commit"]),
            _scalar(optional["sizeof_heap_reserve"]),
            _scalar(optional["sizeof_heap_commit"]),
            _scalar(optional["address_of_entrypoint"]),
            _scalar(optional["base_of_code"]),
            _scalar(optional["image_base"]),
            _scalar(optional["section_alignment"]),
            _scalar(optional["checksum"]),
            _scalar(optional["number_of_rvas_and_sizes"]),
            image_flags,
            dll_flags,
            dos_values,
        ]
    ).astype(np.float32)


def _header_file_info_count_mask() -> np.ndarray:
    coff_mask = [False, True, True, True, False]
    categorical_mask = [False, False]
    version_mask = [False] * _HEADER_VERSION_FIELD_COUNT
    sizeof_mask = [True] * _HEADER_SIZEOF_FIELD_COUNT
    address_mask = [False, False, False, True, False, True]
    return np.hstack(
        [
            coff_mask,
            categorical_mask,
            version_mask,
            sizeof_mask,
            address_mask,
            np.zeros(len(_IMAGE_CHARACTERISTICS), dtype=bool),
            np.zeros(len(_DLL_CHARACTERISTICS), dtype=bool),
            np.zeros(len(_DOS_HEADER_MEMBERS), dtype=bool),
        ]
    )


def _section_info_vector(section: EmberJsonObject) -> np.ndarray:
    sections = cast(EmberJsonObjectList, section.get("sections", []))
    overlay = cast(EmberJsonObject, section.get("overlay", {}))
    entry = cast(str, section.get("entry", ""))
    n_sections = len(sections)
    n_zero_size = sum(1 for item in sections if item["size"] == 0)
    n_empty_name = sum(1 for item in sections if item["name"] == "")
    n_rx = sum(
        1
        for item in sections
        if "MEM_READ" in cast(EmberJsonStringList, item["props"])
        and "MEM_EXECUTE" in cast(EmberJsonStringList, item["props"])
    )
    n_w = sum(1 for item in sections if "MEM_WRITE" in cast(EmberJsonStringList, item["props"]))
    entropies = [_scalar(item["entropy"]) for item in sections] + [
        _scalar(overlay.get("entropy", 0)),
        0.0,
    ]
    size_ratios = [_scalar(item["size_ratio"]) for item in sections] + [
        _scalar(overlay.get("size_ratio", 0)),
        0.0,
    ]
    vsize_ratios = [_scalar(item["vsize_ratio"]) for item in sections] + [0.0]
    general = [
        n_sections,
        n_zero_size,
        n_empty_name,
        n_rx,
        n_w,
        max(entropies),
        min(entropies),
        max(size_ratios),
        min(size_ratios),
        max(vsize_ratios),
        min(vsize_ratios),
    ]
    section_sizes = [(item["name"], item["size"]) for item in sections]
    section_vsizes = [(item["name"], item["vsize"]) for item in sections]
    section_entropies = [(item["name"], item["entropy"]) for item in sections]
    characteristics = [
        f"{item['name']}:{prop}"
        for item in sections
        for prop in cast(EmberJsonStringList, item["props"])
    ]
    size_hash = _hashed_row(
        FeatureHasher(_SECTION_HASH_BUCKETS, input_type="pair"),
        cast(list[JsonEncodableValue], section_sizes),
    )
    vsize_hash = _hashed_row(
        FeatureHasher(_SECTION_HASH_BUCKETS, input_type="pair"),
        cast(list[JsonEncodableValue], section_vsizes),
    )
    entropy_hash = _hashed_row(
        FeatureHasher(_SECTION_HASH_BUCKETS, input_type="pair"),
        cast(list[JsonEncodableValue], section_entropies),
    )
    characteristics_hash = _hashed_row(
        FeatureHasher(_SECTION_CHARACTERISTICS_HASH_BUCKETS, input_type="string"),
        cast(list[JsonEncodableValue], characteristics),
    )
    entry_hash = _hashed_row(
        FeatureHasher(_SECTION_ENTRY_NAME_HASH_BUCKETS, input_type="string"),
        cast(list[JsonEncodableValue], [entry]),
    )
    return np.hstack(
        [
            general,
            size_hash,
            vsize_hash,
            entropy_hash,
            characteristics_hash,
            entry_hash,
            _scalar(overlay.get("size", 0)),
            _scalar(overlay.get("size_ratio", 0)),
            _scalar(overlay.get("entropy", 0)),
        ]
    ).astype(np.float32)


def _section_info_count_mask() -> np.ndarray:
    general_mask = [True, True, True, True, True, False, False, False, False, False, False]
    hash_mask = np.zeros(
        _SECTION_HASH_BUCKETS * _SECTION_HASH_GROUP_TOTAL
        + _SECTION_CHARACTERISTICS_HASH_BUCKETS
        + _SECTION_ENTRY_NAME_HASH_BUCKETS,
        dtype=bool,
    )
    return np.hstack([general_mask, hash_mask, [True, False, False]])


def _imports_info_vector(imports: EmberJsonObject) -> np.ndarray:
    dimension = (
        _IMPORT_SUMMARY_FIELD_COUNT + _IMPORT_LIBRARY_HASH_BUCKETS + _IMPORT_FUNCTION_HASH_BUCKETS
    )
    if not imports:
        return np.zeros(dimension, dtype=np.float32)
    libraries = list({library.lower() for library in imports})
    libraries_hash = _hashed_row(
        FeatureHasher(_IMPORT_LIBRARY_HASH_BUCKETS, input_type="string", alternate_sign=False),
        cast(list[JsonEncodableValue], libraries),
    )
    fully_qualified = [
        f"{library.lower()}:{function}"
        for library, functions in imports.items()
        for function in cast(EmberJsonStringList, functions)
    ]
    imports_hash = _hashed_row(
        FeatureHasher(_IMPORT_FUNCTION_HASH_BUCKETS, input_type="string", alternate_sign=False),
        cast(list[JsonEncodableValue], fully_qualified),
    )
    return np.hstack(
        [float(len(fully_qualified)), float(len(libraries)), libraries_hash, imports_hash]
    ).astype(np.float32)


def _imports_info_count_mask() -> np.ndarray:
    return np.hstack(
        [
            [True, True],
            np.zeros(_IMPORT_LIBRARY_HASH_BUCKETS + _IMPORT_FUNCTION_HASH_BUCKETS, dtype=bool),
        ]
    )


def _exports_info_vector(exports: EmberJsonStringList) -> np.ndarray:
    if not exports:
        return np.zeros(1 + _EXPORT_HASH_BUCKETS, dtype=np.float32)
    exports_hash = _hashed_row(
        FeatureHasher(_EXPORT_HASH_BUCKETS, input_type="string"),
        cast(list[JsonEncodableValue], exports),
    )
    return np.hstack([float(len(exports_hash)), exports_hash]).astype(np.float32)


def _exports_info_count_mask() -> np.ndarray:
    return np.zeros(1 + _EXPORT_HASH_BUCKETS, dtype=bool)


def _data_directories_vector(datadirectories: EmberJsonObjectList) -> np.ndarray:
    dimension = _PAIRED_ENTRY_WIDTH * _DATA_DIRECTORY_COUNT + _PAIRED_ENTRY_WIDTH
    if not datadirectories:
        return np.zeros(dimension, dtype=np.float32)
    features = np.zeros(dimension, dtype=np.float32)
    for entry in datadirectories[1:-1]:
        index = _DATA_DIRECTORY_NAMES.index(cast(str, entry["name"]))
        features[_PAIRED_ENTRY_WIDTH * index] = _scalar(entry["size"])
        features[_PAIRED_ENTRY_WIDTH * index + 1] = _scalar(entry["virtual_address"])
    features[-2] = _scalar(datadirectories[0]["has_relocs"])
    features[-1] = _scalar(datadirectories[0]["has_dynamic_relocs"])
    return features


def _data_directories_count_mask() -> np.ndarray:
    per_directory = [True, False] * _DATA_DIRECTORY_COUNT
    return np.array([*per_directory, False, False])


def _rich_header_vector(richheader: EmberJsonIntegerList) -> np.ndarray:
    dimension = 1 + _RICH_HEADER_HASH_BUCKETS
    if not richheader:
        return np.zeros(dimension, dtype=np.float32)
    number_of_pairs = len(richheader) // _PAIRED_ENTRY_WIDTH
    paired_values = [
        (str(richheader[index]), richheader[index + 1])
        for index in range(0, len(richheader) - 1, _PAIRED_ENTRY_WIDTH)
    ]
    paired_hash = _hashed_row(
        FeatureHasher(_RICH_HEADER_HASH_BUCKETS, input_type="pair"),
        cast(list[JsonEncodableValue], paired_values),
    )
    return np.hstack([float(number_of_pairs), paired_hash]).astype(np.float32)


def _rich_header_count_mask() -> np.ndarray:
    return np.hstack([[True], np.zeros(_RICH_HEADER_HASH_BUCKETS, dtype=bool)])


def _authenticode_vector(authenticode: EmberJsonObject) -> np.ndarray:
    if not authenticode:
        return np.zeros(_AUTHENTICODE_DIMENSION, dtype=np.float32)
    return np.array(
        [
            authenticode["num_certs"],
            authenticode["self_signed"],
            authenticode["empty_program_name"],
            authenticode["no_countersigner"],
            authenticode["parse_error"],
            authenticode["chain_max_depth"],
            authenticode["latest_signing_time"],
            authenticode["signing_time_diff"],
        ],
        dtype=np.float32,
    )


def _authenticode_count_mask() -> np.ndarray:
    return np.array([True, False, False, False, False, True, False, False])


def _pefile_warnings_vector(warnings: EmberJsonStringList) -> np.ndarray:
    vector = np.zeros(_PEFILE_WARNING_DIMENSION, dtype=np.float32)
    if not warnings:
        return vector
    for warning in warnings:
        index = _PEFILE_WARNING_INDEX.get(warning)
        if index is not None:
            vector[index] = 1.0
    vector[-1] = len(warnings)
    return vector


def _pefile_warnings_count_mask() -> np.ndarray:
    mask = np.zeros(_PEFILE_WARNING_DIMENSION, dtype=bool)
    mask[-1] = True
    return mask


def _ember2024_feature_vector(record: EmberJsonObject) -> np.ndarray:
    return np.hstack(
        [
            _general_file_info_vector(cast(EmberJsonObject, record["general"])),
            _normalized_histogram_vector(cast(EmberJsonIntegerList, record["histogram"])),
            _normalized_histogram_vector(cast(EmberJsonIntegerList, record["byteentropy"])),
            _string_extractor_vector(cast(EmberJsonObject, record["strings"])),
            _header_file_info_vector(cast(EmberJsonObject, record["header"])),
            _section_info_vector(cast(EmberJsonObject, record["section"])),
            _imports_info_vector(cast(EmberJsonObject, record["imports"])),
            _exports_info_vector(cast(EmberJsonStringList, record["exports"])),
            _data_directories_vector(cast(EmberJsonObjectList, record["datadirectories"])),
            _rich_header_vector(cast(EmberJsonIntegerList, record["richheader"])),
            _authenticode_vector(cast(EmberJsonObject, record["authenticode"])),
            _pefile_warnings_vector(cast(EmberJsonStringList, record["pefilewarnings"])),
        ]
    ).astype(np.float32)


def ember2024_count_feature_mask() -> np.ndarray:
    return np.hstack(
        [
            _general_file_info_count_mask(),
            np.zeros(256, dtype=bool),
            np.zeros(256, dtype=bool),
            _string_extractor_count_mask(),
            _header_file_info_count_mask(),
            _section_info_count_mask(),
            _imports_info_count_mask(),
            _exports_info_count_mask(),
            _data_directories_count_mask(),
            _rich_header_count_mask(),
            _authenticode_count_mask(),
            _pefile_warnings_count_mask(),
        ]
    )


@dataclass(frozen=True)
class EmberRawRecord:
    sample_hash: SampleIdentifier
    year_month: CalendarMonthString
    label: BinaryLabel | None
    family: FamilyName | None


@dataclass(frozen=True)
class LoadedEmberDataset:
    records: tuple[EmberRawRecord, ...]
    features: np.ndarray


def _year_month_from_epoch_seconds(epoch_seconds: EpochSeconds) -> CalendarMonthString:
    moment = datetime.fromtimestamp(epoch_seconds, tz=UTC)
    return f"{moment.year:04d}-{moment.month:02d}"


def _parse_record(payload: EmberJsonObject) -> tuple[EmberRawRecord, np.ndarray]:
    sha256 = cast(str, payload["sha256"])
    raw_label = _scalar(payload["label"])
    submission_epoch = _scalar(payload["first_submission_date"])
    family = cast(str | None, payload.get("family"))
    record = EmberRawRecord(
        sample_hash=SampleIdentifier(sha256),
        year_month=_year_month_from_epoch_seconds(submission_epoch),
        label=None if raw_label < 0 else raw_label > 0,
        family=family,
    )
    return record, _ember2024_feature_vector(payload)


def load_ember2024_records(data_directory: Path) -> LoadedEmberDataset:
    feature_dimension = ember2024_count_feature_mask().size
    jsonl_files = sorted(data_directory.glob("*.jsonl"))
    if not jsonl_files:
        return LoadedEmberDataset(records=(), features=np.zeros((0, feature_dimension)))
    records: list[EmberRawRecord] = []
    feature_rows: list[np.ndarray] = []
    for jsonl_file in jsonl_files:
        with jsonl_file.open(encoding="utf-8") as jsonl_stream:
            for line in jsonl_stream:
                stripped = line.strip()
                if not stripped:
                    continue
                payload = EmberJsonObject(cast(dict[str, JsonEncodableValue], json.loads(stripped)))
                record, feature_row = _parse_record(payload)
                records.append(record)
                feature_rows.append(feature_row)
    features = np.stack(feature_rows).astype(np.float32)
    return LoadedEmberDataset(records=tuple(records), features=features)


def apply_log1p_transforms(features: np.ndarray, count_feature_mask: np.ndarray) -> np.ndarray:
    transformed = features.copy()
    transformed[:, count_feature_mask] = np.log1p(np.maximum(features[:, count_feature_mask], 0.0))
    return transformed


def standardize_ember_features(features: np.ndarray) -> np.ndarray:
    if features.shape[0] == 0:
        return features
    mean = np.mean(features, axis=0)
    std = np.std(features, axis=0)
    std[std < 1e-12] = 1.0
    return (features - mean) / std


class EmberValidationError(ValueError):
    pass


def validate_ember_dataset(dataset: LoadedEmberDataset) -> None:
    if len(dataset.records) != dataset.features.shape[0]:
        raise EmberValidationError("record count and feature rows must match")


def run_empty_ember_transform_audit() -> None:
    empty = LoadedEmberDataset(records=(), features=np.zeros((0, 0), dtype=np.float32))
    validate_ember_dataset(empty)
    transformed = apply_log1p_transforms(empty.features, np.zeros(0, dtype=bool))
    standardized = standardize_ember_features(transformed)
    if standardized.shape[0] < 0:
        raise EmberValidationError("EMBER standardization produced an impossible shape")


WeekIdentifier = NewType("WeekIdentifier", str)
CalendarMonthCell = NewType("CalendarMonthCell", str)


@dataclass(frozen=True)
class EmberControlRecord:
    sample_hash: SampleIdentifier
    format_client: DetailMessage
    collection_week: WeekIdentifier
    family: FamilyName | None


def conservative_timestamp_month(collection_week: WeekIdentifier) -> WeekIdentifier:
    return collection_week


def monthly_matching_cell(collection_week: WeekIdentifier) -> CalendarMonthCell:
    return CalendarMonthCell(collection_week[:7])


@dataclass(frozen=True)
class ControlMatchingLevel:
    weekly: ValidationFlag


def choose_control_matching_level(
    weekly_support_per_side: SampleCount,
    minimum_support_per_class: SupportThreshold,
    monthly_support_per_side: SampleCount,
) -> ControlMatchingLevel | None:
    if weekly_support_per_side >= minimum_support_per_class:
        return ControlMatchingLevel(weekly=True)
    if monthly_support_per_side >= minimum_support_per_class:
        return ControlMatchingLevel(weekly=False)
    return None


@dataclass(frozen=True)
class EmberControlMatch:
    malicious_sample_id: SampleIdentifier
    control_sample_id: SampleIdentifier
    matched_week: CalendarMonthString | None
    matched_month: CalendarMonthString | None
    weekly_level: ValidationFlag


def _matching_key(
    level: ControlMatchingLevel,
) -> Callable[[EmberControlRecord], CalendarMonthCell | WeekIdentifier]:
    if level.weekly:
        return lambda record: record.collection_week
    return lambda record: monthly_matching_cell(record.collection_week)


def match_ember_controls(
    malicious: tuple[EmberControlRecord, ...],
    controls: tuple[EmberControlRecord, ...],
    level: ControlMatchingLevel,
) -> tuple[EmberControlMatch, ...]:
    key = _matching_key(level)
    controls_by_cell: dict[str, list[EmberControlRecord]] = {}
    for control in controls:
        controls_by_cell.setdefault(str(key(control)), []).append(control)
    matches: list[EmberControlMatch] = []
    used: set[SampleIdentifier] = set()
    for record in malicious:
        candidates = [
            control
            for control in controls_by_cell.get(str(key(record)), [])
            if control.sample_hash not in used
        ]
        for control in candidates[:1]:
            used.add(control.sample_hash)
            matches.append(
                EmberControlMatch(
                    malicious_sample_id=record.sample_hash,
                    control_sample_id=control.sample_hash,
                    matched_week=control.collection_week if level.weekly else None,
                    matched_month=None if level.weekly else str(key(record)),
                    weekly_level=level.weekly,
                )
            )
    return tuple(matches)


def ember_client_semantics(
    observed_format_clients: tuple[ConfirmatoryFormat, ...],
) -> ClientSemanticsAudit:
    return ClientSemanticsAudit(
        dataset=DatasetSelector.EMBER2024,
        source_field="format_client",
        classification=ClientSemanticsClass.DIAGNOSTIC_PARTITION,
        observed_values=tuple(observed_format_clients),
        supports_natural_federation_claim=False,
    )


PeFileBytes = NewType("PeFileBytes", bytes)


class PeMutationError(RuntimeError):
    pass


PayloadBytes = NewType("PayloadBytes", int)

PE_PAYLOAD_SIZES: tuple[PayloadBytes, ...] = (
    PayloadBytes(64),
    PayloadBytes(256),
    PayloadBytes(1024),
)

APK_PAYLOAD_SIZES: tuple[PayloadBytes, ...] = (
    PayloadBytes(256),
    PayloadBytes(1024),
    PayloadBytes(4096),
)

CompositionLength = NewType("CompositionLength", int)


class PeImportName(StrEnum):
    GET_VERSION = "GetVersion"
    GET_TICK_COUNT = "GetTickCount"
    GET_LAST_ERROR = "GetLastError"
    CLOSE_HANDLE = "CloseHandle"


class PeSectionRenameTarget(StrEnum):
    DATA1 = ".data1"
    RDATA1 = ".rdata1"
    TEXT1 = ".text1"


class UpxAction(StrEnum):
    PACK = "pack"
    UNPACK = "unpack"


@dataclass(frozen=True)
class DisplacementVector:
    components: tuple[DisplacementComponent, ...]

    def displacement_norm(self) -> NormValue:
        squared = sum(component * component for component in self.components)
        value: NormValue = math.sqrt(squared)
        return value

    def normalized(self) -> DisplacementVector:
        norm = self.displacement_norm()
        if norm <= 0.0:
            raise ValueError("cannot normalize a zero displacement vector")
        return DisplacementVector(components=tuple(c / norm for c in self.components))


def is_degenerate_displacement(
    vector: DisplacementVector, floor: ZeroDisplacementFloor
) -> DegeneracyFlag:
    return vector.displacement_norm() < floor


def _load_pe(pe_bytes: PeFileBytes) -> lief.PE.Binary:
    binary = lief.PE.parse(list(pe_bytes))
    if binary is None:
        raise PeMutationError("input bytes are not a valid PE file")
    return binary


def _dump_pe(binary: lief.PE.Binary, *, rebuild_imports: bool = False) -> PeFileBytes:
    config = lief.PE.Builder.config_t()
    config.imports = rebuild_imports
    builder = lief.PE.Builder(binary, config)
    builder.build()
    return PeFileBytes(bytes(builder.raw_bytes()))


def append_benign_eof_bytes(pe_bytes: PeFileBytes, payload_size: PayloadBytes) -> PeFileBytes:
    return PeFileBytes(bytes(pe_bytes) + bytes(payload_size))


def fill_existing_section_slack(pe_bytes: PeFileBytes, payload_size: PayloadBytes) -> PeFileBytes:
    binary = _load_pe(pe_bytes)
    if not binary.sections:
        raise PeMutationError("binary has no sections to fill")
    target = max(binary.sections, key=lambda section: section.size - section.virtual_size)
    slack = target.size - target.virtual_size
    if slack <= 0:
        raise PeMutationError("no section slack available to fill")
    fill_length = min(payload_size, slack)
    content = list(target.content)
    content[target.virtual_size : target.virtual_size + fill_length] = [0x90] * fill_length
    target.content = content
    return _dump_pe(binary)


def add_unused_import(pe_bytes: PeFileBytes, import_name: PeImportName) -> PeFileBytes:
    binary = _load_pe(pe_bytes)
    library = binary.get_import("KERNEL32.dll")
    if library is None:
        library = binary.add_import("KERNEL32.dll")
    library.add_entry(import_name)
    return _dump_pe(binary, rebuild_imports=True)


def rename_section(pe_bytes: PeFileBytes, target: PeSectionRenameTarget) -> PeFileBytes:
    binary = _load_pe(pe_bytes)
    if not binary.sections:
        raise PeMutationError("binary has no sections to rename")
    section = binary.sections[-1]
    section.name = target
    return _dump_pe(binary)


def add_read_only_section(pe_bytes: PeFileBytes, payload_size: PayloadBytes) -> PeFileBytes:
    binary = _load_pe(pe_bytes)
    section = lief.PE.Section(".fdroro")
    section.content = [0] * payload_size
    section.characteristics = int(lief.PE.Section.CHARACTERISTICS.MEM_READ) | int(
        lief.PE.Section.CHARACTERISTICS.CNT_INITIALIZED_DATA
    )
    binary.add_section(section)
    return _dump_pe(binary)


_JMP_REL32_OPCODE_OFFSET = 2
_JMP_REL32_INSTRUCTION_LENGTH = 5


def add_entry_point_trampoline(pe_bytes: PeFileBytes) -> PeFileBytes:
    binary = _load_pe(pe_bytes)
    original_entry_rva = binary.optional_header.addressof_entrypoint
    section = lief.PE.Section(".fdtramp")
    section.characteristics = (
        int(lief.PE.Section.CHARACTERISTICS.MEM_READ)
        | int(lief.PE.Section.CHARACTERISTICS.MEM_EXECUTE)
        | int(lief.PE.Section.CHARACTERISTICS.CNT_CODE)
    )
    section.content = [0x90, 0x90, 0xE9, 0x00, 0x00, 0x00, 0x00]
    added = binary.add_section(section)
    if added is None:
        raise PeMutationError("failed to add entry-point trampoline section")
    jump_instruction_rva = added.virtual_address + _JMP_REL32_OPCODE_OFFSET
    relative_offset = original_entry_rva - (jump_instruction_rva + _JMP_REL32_INSTRUCTION_LENGTH)
    packed_offset = struct.pack("<i", relative_offset)
    content = list(added.content)
    content[3:7] = list(packed_offset)
    added.content = content
    binary.optional_header.addressof_entrypoint = added.virtual_address
    return _dump_pe(binary)


def remove_authenticode_directory(pe_bytes: PeFileBytes) -> PeFileBytes:
    binary = _load_pe(pe_bytes)
    directory = binary.data_directory(lief.PE.DataDirectory.TYPES.CERTIFICATE_TABLE)
    if directory is None:
        raise PeMutationError("binary has no certificate-table data directory")
    directory.rva = 0
    directory.size = 0
    return _dump_pe(binary)


def zero_pe_checksum(pe_bytes: PeFileBytes) -> PeFileBytes:
    binary = _load_pe(pe_bytes)
    binary.optional_header.checksum = 0
    return _dump_pe(binary)


def remove_debug_directory(pe_bytes: PeFileBytes) -> PeFileBytes:
    binary = _load_pe(pe_bytes)
    binary.clear_debug()
    return _dump_pe(binary)


def apply_upx_action(pe_bytes: PeFileBytes, action: UpxAction) -> PeFileBytes:
    upx_path = shutil.which("upx")
    if upx_path is None:
        raise PeMutationError("upx toolchain is not available on PATH")
    with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
        temp_file.write(bytes(pe_bytes))
        temp_path = Path(temp_file.name)
    try:
        flag = "-d" if action is UpxAction.UNPACK else "--best"
        result = subprocess.run(
            [upx_path, flag, str(temp_path)], capture_output=True, timeout=30, check=False
        )
        if result.returncode != 0:
            raise PeMutationError(f"upx failed: {result.stderr.decode(errors='replace')}")
        return PeFileBytes(temp_path.read_bytes())
    finally:
        temp_path.unlink(missing_ok=True)
