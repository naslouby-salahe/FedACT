from __future__ import annotations

import shutil
import struct
import subprocess
import tempfile
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Annotated, NewType

import lief
from pydantic import Field

from fedact.domain.operators.contracts import (
    NormalizedParameterString,
    OperatorDomain,
    OperatorFamily,
)
from fedact.domain.types import DegeneracyFlag

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

DisplacementNorm = Annotated[float, Field(ge=0.0)]
ZeroDisplacementFloor = Annotated[float, Field(gt=0.0)]
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
    components: tuple[float, ...]

    def displacement_norm(self) -> DisplacementNorm:
        squared = sum(component * component for component in self.components)
        value: DisplacementNorm = squared**0.5
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
    return PeFileBytes(bytes(pe_bytes) + bytes(int(payload_size)))


def fill_existing_section_slack(pe_bytes: PeFileBytes, payload_size: PayloadBytes) -> PeFileBytes:
    binary = _load_pe(pe_bytes)
    if not binary.sections:
        raise PeMutationError("binary has no sections to fill")
    target = max(binary.sections, key=lambda section: section.size - section.virtual_size)
    slack = target.size - target.virtual_size
    if slack <= 0:
        raise PeMutationError("no section slack available to fill")
    fill_length = min(int(payload_size), slack)
    content = list(target.content)
    content[target.virtual_size : target.virtual_size + fill_length] = [0x90] * fill_length
    target.content = content
    return _dump_pe(binary)


def add_unused_import(pe_bytes: PeFileBytes, import_name: PeImportName) -> PeFileBytes:
    binary = _load_pe(pe_bytes)
    library = binary.get_import("KERNEL32.dll")
    if library is None:
        library = binary.add_import("KERNEL32.dll")
    library.add_entry(import_name.value)
    return _dump_pe(binary, rebuild_imports=True)


def rename_section(pe_bytes: PeFileBytes, target: PeSectionRenameTarget) -> PeFileBytes:
    binary = _load_pe(pe_bytes)
    if not binary.sections:
        raise PeMutationError("binary has no sections to rename")
    section = binary.sections[-1]
    section.name = target.value
    return _dump_pe(binary)


def add_read_only_section(pe_bytes: PeFileBytes, payload_size: PayloadBytes) -> PeFileBytes:
    binary = _load_pe(pe_bytes)
    section = lief.PE.Section(".fdroro")
    section.content = [0] * int(payload_size)
    section.characteristics = int(lief.PE.Section.CHARACTERISTICS.MEM_READ) | int(
        lief.PE.Section.CHARACTERISTICS.CNT_INITIALIZED_DATA
    )
    binary.add_section(section)
    return _dump_pe(binary)


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
    jump_instruction_rva = added.virtual_address + 2
    relative_offset = original_entry_rva - (jump_instruction_rva + 5)
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


def pe_mutation_families() -> tuple[OperatorFamily, ...]:
    return (
        OperatorFamily(
            name="append-benign-eof-bytes",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=0,
            parameter_grid=tuple(
                NormalizedParameterString(f"payload={size}") for size in sorted(PE_PAYLOAD_SIZES)
            ),
        ),
        OperatorFamily(
            name="fill-existing-section-slack",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=1,
            parameter_grid=tuple(
                NormalizedParameterString(f"payload={size} (truncated to available slack)")
                for size in sorted(PE_PAYLOAD_SIZES)
            ),
        ),
        OperatorFamily(
            name="add-unused-import",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=2,
            parameter_grid=tuple(
                NormalizedParameterString(f"import={name.value}")
                for name in sorted(PeImportName, key=lambda item: item.value)
            ),
        ),
        OperatorFamily(
            name="rename-section",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=3,
            parameter_grid=tuple(
                NormalizedParameterString(f"section={item.value}")
                for item in sorted(PeSectionRenameTarget, key=lambda item: item.value)
            ),
        ),
        OperatorFamily(
            name="add-read-only-section",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=4,
            parameter_grid=tuple(
                NormalizedParameterString(f"payload={size}") for size in (256, 1024)
            ),
        ),
        OperatorFamily(
            name="entry-point-trampoline",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=5,
            parameter_grid=(NormalizedParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name="remove-authenticode-directory",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=6,
            parameter_grid=(NormalizedParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name="zero-pe-checksum",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=7,
            parameter_grid=(NormalizedParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name="remove-debug-directory",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=8,
            parameter_grid=(NormalizedParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name="upx-pack-unpack",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=9,
            parameter_grid=tuple(
                NormalizedParameterString(f"action={item.value}")
                for item in sorted(UpxAction, key=lambda item: item.value)
            ),
        ),
    )
