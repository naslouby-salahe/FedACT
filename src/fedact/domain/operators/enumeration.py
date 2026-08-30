from __future__ import annotations

from itertools import combinations
from typing import Annotated

from pydantic import Field

from fedact.domain.operators.contracts import (
    NormalizedParameterString,
    OperatorCandidate,
    OperatorComposition,
    OperatorFamily,
)
from fedact.domain.records import SampleIdentifier, SplitCutoffIdentity


class EnumerationContractError(ValueError):
    pass


def _normalized_form(
    families: tuple[OperatorFamily, ...], parameters: tuple[NormalizedParameterString, ...]
) -> str:
    pairs = zip(families, parameters, strict=True)
    parts = [f"{family.name}={parameter}" for family, parameter in pairs]
    return "|".join(parts)


def _ordered_composition(
    families: tuple[OperatorFamily, ...], parameters: tuple[NormalizedParameterString, ...]
) -> OperatorComposition:
    paired = sorted(zip(families, parameters, strict=True), key=lambda pair: pair[0].listed_order)
    ordered_families = tuple(family for family, _unused in paired)
    ordered_parameters = tuple(parameter for _unused, parameter in paired)
    return OperatorComposition(families=ordered_families, parameters=ordered_parameters)


def _compositions_of_length(
    selections: tuple[tuple[OperatorFamily, NormalizedParameterString], ...],
    length: int,
) -> list[OperatorComposition]:
    compositions: list[OperatorComposition] = []
    for chosen in combinations(selections, length):
        chosen_families = tuple(family for family, _unused in chosen)
        names = [family.name for family in chosen_families]
        if len(set(names)) != len(names):
            continue
        parameters = tuple(parameter for _unused, parameter in chosen)
        compositions.append(_ordered_composition(chosen_families, parameters))
    return compositions


MaximumCompositionLength = Annotated[int, Field(ge=1)]


def enumerate_candidates(
    families: tuple[OperatorFamily, ...],
    maximum_composed_atomic_actions: MaximumCompositionLength,
    source_sample_id: SampleIdentifier,
    cutoff_identity: SplitCutoffIdentity,
) -> tuple[OperatorCandidate, ...]:
    if maximum_composed_atomic_actions < 1:
        raise EnumerationContractError("maximum composed atomic actions must be at least one")
    ordered_families = tuple(sorted(families, key=lambda family: family.listed_order))
    listed_orders = [family.listed_order for family in ordered_families]
    if len(set(listed_orders)) != len(listed_orders):
        raise EnumerationContractError("operator families must have unique listed orders")
    selections: list[tuple[OperatorFamily, NormalizedParameterString]] = []
    for family in ordered_families:
        for parameter in sorted(family.parameter_grid):
            selections.append((family, parameter))

    candidates: list[OperatorCandidate] = []
    seen: set[str] = set()
    for length in range(1, maximum_composed_atomic_actions + 1):
        for composition in _compositions_of_length(tuple(selections), length):
            canonical = _normalized_form(composition.families, composition.parameters)
            if canonical in seen:
                continue
            seen.add(canonical)
            candidates.append(
                OperatorCandidate(
                    composition=composition,
                    normalized_form=canonical,
                    source_sample_id=source_sample_id,
                    cutoff_identity=cutoff_identity,
                )
            )
    return tuple(candidates)
