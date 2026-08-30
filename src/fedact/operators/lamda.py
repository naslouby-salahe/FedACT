from __future__ import annotations

from typing import NewType

from fedact.domain.operators.contracts import (
    NormalizedParameterString,
    OperatorDomain,
    OperatorFamily,
)
from fedact.operators.pe_mutations import APK_PAYLOAD_SIZES, PayloadBytes

BENIGN_GADGET_LIBRARY = "cutoff-safe-benign-gadget-library"


def lamda_families() -> tuple[OperatorFamily, ...]:
    return (
        OperatorFamily(
            name="unreachable-benign-gadget-injection",
            domain=OperatorDomain.ANDROID_APK,
            listed_order=0,
            parameter_grid=(NormalizedParameterString(f"gadget-library={BENIGN_GADGET_LIBRARY}"),),
        ),
        OperatorFamily(
            name="permission-neutral-resource-injection",
            domain=OperatorDomain.ANDROID_APK,
            listed_order=1,
            parameter_grid=tuple(
                NormalizedParameterString(f"payload={size}") for size in sorted(APK_PAYLOAD_SIZES)
            ),
        ),
    )


GadgetLibraryIdentity = NewType("GadgetLibraryIdentity", str)


def gadget_library_identity() -> GadgetLibraryIdentity:
    return GadgetLibraryIdentity(BENIGN_GADGET_LIBRARY)


_ = PayloadBytes
