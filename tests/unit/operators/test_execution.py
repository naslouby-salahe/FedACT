from __future__ import annotations

from pathlib import Path

import pytest

from fedact.operators.common import NormalizedParameterString, OperatorFamily
from fedact.operators.common import OperatorDomain as Domain
from fedact.operators.ember2024 import (
    PeFileBytes,
    UnsupportedOperatorFamilyError,
    apply_and_verify_pe_operator_family,
    pe_mutation_families,
)

SAMPLE_PE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "sample_pe.exe"


@pytest.fixture
def sample_pe_bytes() -> PeFileBytes:
    return PeFileBytes(SAMPLE_PE_PATH.read_bytes())


def test_every_pe_family_except_upx_applies_and_stays_structurally_valid(
    sample_pe_bytes: PeFileBytes,
) -> None:
    for family in pe_mutation_families():
        if family.name == "upx-pack-unpack":
            continue
        parameter = family.parameter_grid[0]
        mutated = apply_and_verify_pe_operator_family(family, parameter, sample_pe_bytes)
        assert len(mutated) > 0


def test_unsupported_family_is_rejected(sample_pe_bytes: PeFileBytes) -> None:
    bogus_family = OperatorFamily(
        name="not-a-real-family",
        domain=Domain.WINDOWS_PE,
        listed_order=99,
        parameter_grid=(NormalizedParameterString("no-parameter"),),
    )
    with pytest.raises(UnsupportedOperatorFamilyError):
        apply_and_verify_pe_operator_family(
            bogus_family, bogus_family.parameter_grid[0], sample_pe_bytes
        )
