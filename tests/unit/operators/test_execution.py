from __future__ import annotations

from pathlib import Path

import pytest

from fedact.certification.actions import OperatorDomain as Domain
from fedact.certification.actions import (
    apply_and_verify_pe_operator_family,
    lamda_families,
    pe_mutation_families,
)
from fedact.domain.types import ApkOperatorFamilyName, PeFileBytes, PeOperatorFamilyName

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


def test_pe_and_apk_operator_family_names_are_disjoint() -> None:
    pe_names = {family.name for family in pe_mutation_families()}
    apk_names = {family.name for family in lamda_families()}
    assert pe_names.isdisjoint(apk_names)
    assert pe_names <= set(PeOperatorFamilyName)
    assert apk_names <= set(ApkOperatorFamilyName)
    assert {family.domain for family in pe_mutation_families()} == {Domain.WINDOWS_PE}
    assert {family.domain for family in lamda_families()} == {Domain.ANDROID_APK}
