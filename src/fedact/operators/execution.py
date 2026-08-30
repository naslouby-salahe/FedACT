from __future__ import annotations

import lief

from fedact.domain.operators.contracts import NormalizedParameterString, OperatorFamily
from fedact.operators.pe_mutations import (
    PayloadBytes,
    PeFileBytes,
    PeImportName,
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


class UnsupportedOperatorFamilyError(ValueError):
    pass


class MutationStructuralIntegrityError(ValueError):
    pass


def _parameter_value(parameter: NormalizedParameterString) -> str:
    if "=" not in parameter:
        return parameter
    return parameter.split("=", 1)[1].split(" ", 1)[0]


def apply_pe_operator_family(
    family: OperatorFamily, parameter: NormalizedParameterString, pe_bytes: PeFileBytes
) -> PeFileBytes:
    value = _parameter_value(parameter)
    if family.name == "append-benign-eof-bytes":
        return append_benign_eof_bytes(pe_bytes, PayloadBytes(int(value)))
    if family.name == "fill-existing-section-slack":
        return fill_existing_section_slack(pe_bytes, PayloadBytes(int(value)))
    if family.name == "add-unused-import":
        return add_unused_import(pe_bytes, PeImportName(value))
    if family.name == "rename-section":
        return rename_section(pe_bytes, PeSectionRenameTarget(value))
    if family.name == "add-read-only-section":
        return add_read_only_section(pe_bytes, PayloadBytes(int(value)))
    if family.name == "entry-point-trampoline":
        return add_entry_point_trampoline(pe_bytes)
    if family.name == "remove-authenticode-directory":
        return remove_authenticode_directory(pe_bytes)
    if family.name == "zero-pe-checksum":
        return zero_pe_checksum(pe_bytes)
    if family.name == "remove-debug-directory":
        return remove_debug_directory(pe_bytes)
    if family.name == "upx-pack-unpack":
        return apply_upx_action(pe_bytes, UpxAction(value))
    raise UnsupportedOperatorFamilyError(f"unsupported PE operator family: {family.name}")


def apply_and_verify_pe_operator_family(
    family: OperatorFamily, parameter: NormalizedParameterString, pe_bytes: PeFileBytes
) -> PeFileBytes:
    mutated = apply_pe_operator_family(family, parameter, pe_bytes)
    if lief.PE.parse(list(mutated)) is None:
        raise MutationStructuralIntegrityError(
            f"mutation family {family.name!r} produced a structurally invalid PE file"
        )
    return mutated
