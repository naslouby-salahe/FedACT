from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, NewType

from pydantic import Field

from fedact.domain.operators.contracts import (
    CanonicalParameterString,
    OperatorDomain,
    OperatorFamily,
)

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


def is_degenerate_displacement(vector: DisplacementVector, floor: ZeroDisplacementFloor) -> bool:
    return vector.displacement_norm() < floor


def pe_mutation_families() -> tuple[OperatorFamily, ...]:
    return (
        OperatorFamily(
            name="append-benign-eof-bytes",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=0,
            parameter_grid=tuple(
                CanonicalParameterString(f"payload={size}") for size in sorted(PE_PAYLOAD_SIZES)
            ),
        ),
        OperatorFamily(
            name="fill-existing-section-slack",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=1,
            parameter_grid=tuple(
                CanonicalParameterString(f"payload={size} (truncated to available slack)")
                for size in sorted(PE_PAYLOAD_SIZES)
            ),
        ),
        OperatorFamily(
            name="add-unused-import",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=2,
            parameter_grid=tuple(
                CanonicalParameterString(f"import={name.value}")
                for name in sorted(PeImportName, key=lambda item: item.value)
            ),
        ),
        OperatorFamily(
            name="rename-section",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=3,
            parameter_grid=tuple(
                CanonicalParameterString(f"section={item.value}")
                for item in sorted(PeSectionRenameTarget, key=lambda item: item.value)
            ),
        ),
        OperatorFamily(
            name="add-read-only-section",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=4,
            parameter_grid=tuple(
                CanonicalParameterString(f"payload={size}") for size in (256, 1024)
            ),
        ),
        OperatorFamily(
            name="entry-point-trampoline",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=5,
            parameter_grid=(CanonicalParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name="remove-authenticode-directory",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=6,
            parameter_grid=(CanonicalParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name="zero-pe-checksum",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=7,
            parameter_grid=(CanonicalParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name="remove-debug-directory",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=8,
            parameter_grid=(CanonicalParameterString("no-parameter"),),
        ),
        OperatorFamily(
            name="upx-pack-unpack",
            domain=OperatorDomain.WINDOWS_PE,
            listed_order=9,
            parameter_grid=tuple(
                CanonicalParameterString(f"action={item.value}")
                for item in sorted(UpxAction, key=lambda item: item.value)
            ),
        ),
    )
