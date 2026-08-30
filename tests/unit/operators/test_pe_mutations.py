from __future__ import annotations

import shutil
from pathlib import Path

import lief
import pytest

from fedact.operators.pe_mutations import (
    PayloadBytes,
    PeFileBytes,
    PeImportName,
    PeMutationError,
    PeSectionRenameTarget,
    UpxAction,
    add_entry_point_trampoline,
    add_read_only_section,
    add_unused_import,
    append_benign_eof_bytes,
    apply_upx_action,
    fill_existing_section_slack,
    remove_authenticode_directory,
    remove_debug_directory,
    rename_section,
    zero_pe_checksum,
)

SAMPLE_PE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "sample_pe.exe"


@pytest.fixture
def sample_pe_bytes() -> PeFileBytes:
    return PeFileBytes(SAMPLE_PE_PATH.read_bytes())


def test_append_benign_eof_bytes_extends_the_file(sample_pe_bytes: PeFileBytes) -> None:
    mutated = append_benign_eof_bytes(sample_pe_bytes, PayloadBytes(64))
    assert len(mutated) == len(sample_pe_bytes) + 64
    assert lief.PE.parse(list(mutated)) is not None


def test_fill_existing_section_slack_stays_a_valid_pe(sample_pe_bytes: PeFileBytes) -> None:
    mutated = fill_existing_section_slack(sample_pe_bytes, PayloadBytes(20))
    binary = lief.PE.parse(list(mutated))
    assert binary is not None


def test_add_unused_import_adds_a_real_iat_entry(sample_pe_bytes: PeFileBytes) -> None:
    mutated = add_unused_import(sample_pe_bytes, PeImportName.GET_VERSION)
    binary = lief.PE.parse(list(mutated))
    assert binary is not None
    library = binary.get_import("KERNEL32.dll")
    assert library is not None
    assert "GetVersion" in [entry.name for entry in library.entries]


def test_rename_section_changes_the_last_section_name(sample_pe_bytes: PeFileBytes) -> None:
    mutated = rename_section(sample_pe_bytes, PeSectionRenameTarget.DATA1)
    binary = lief.PE.parse(list(mutated))
    assert binary is not None
    assert binary.sections[-1].name == ".data1"


def test_add_read_only_section_appends_a_new_section(sample_pe_bytes: PeFileBytes) -> None:
    before = lief.PE.parse(list(sample_pe_bytes))
    assert before is not None
    before_count = len(before.sections)
    mutated = add_read_only_section(sample_pe_bytes, PayloadBytes(256))
    after = lief.PE.parse(list(mutated))
    assert after is not None
    assert len(after.sections) == before_count + 1


def test_add_entry_point_trampoline_redirects_execution(sample_pe_bytes: PeFileBytes) -> None:
    before = lief.PE.parse(list(sample_pe_bytes))
    assert before is not None
    original_entry_rva = before.optional_header.addressof_entrypoint
    mutated = add_entry_point_trampoline(sample_pe_bytes)
    after = lief.PE.parse(list(mutated))
    assert after is not None
    new_entry_rva = after.optional_header.addressof_entrypoint
    assert new_entry_rva != original_entry_rva
    trampoline_section = after.section_from_rva(new_entry_rva)
    assert trampoline_section is not None
    assert trampoline_section.name == ".fdtramp"


def test_remove_authenticode_directory_clears_the_certificate_table(
    sample_pe_bytes: PeFileBytes,
) -> None:
    mutated = remove_authenticode_directory(sample_pe_bytes)
    binary = lief.PE.parse(list(mutated))
    assert binary is not None
    directory = binary.data_directory(lief.PE.DataDirectory.TYPES.CERTIFICATE_TABLE)
    assert directory is not None
    assert directory.rva == 0
    assert directory.size == 0


def test_zero_pe_checksum_clears_the_checksum(sample_pe_bytes: PeFileBytes) -> None:
    mutated = zero_pe_checksum(sample_pe_bytes)
    binary = lief.PE.parse(list(mutated))
    assert binary is not None
    assert binary.optional_header.checksum == 0


def test_remove_debug_directory_clears_debug_entries(sample_pe_bytes: PeFileBytes) -> None:
    mutated = remove_debug_directory(sample_pe_bytes)
    binary = lief.PE.parse(list(mutated))
    assert binary is not None
    directory = binary.data_directory(lief.PE.DataDirectory.TYPES.DEBUG_DIR)
    assert directory is not None
    assert directory.rva == 0
    assert directory.size == 0


def test_mutation_rejects_non_pe_bytes() -> None:
    with pytest.raises(PeMutationError):
        zero_pe_checksum(PeFileBytes(b"not a pe file"))


@pytest.mark.skipif(shutil.which("upx") is None, reason="upx is not installed")
def test_apply_upx_action_packs_a_real_binary(sample_pe_bytes: PeFileBytes) -> None:
    mutated = apply_upx_action(sample_pe_bytes, UpxAction.PACK)
    assert lief.PE.parse(list(mutated)) is not None


@pytest.mark.skipif(shutil.which("upx") is not None, reason="upx is installed")
def test_apply_upx_action_reports_missing_toolchain(sample_pe_bytes: PeFileBytes) -> None:
    with pytest.raises(PeMutationError, match="upx toolchain is not available"):
        apply_upx_action(sample_pe_bytes, UpxAction.PACK)
