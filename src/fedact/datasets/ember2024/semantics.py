from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, NewType

from pydantic import Field

from fedact.config.models import PositiveInt
from fedact.datasets.records import (
    ClientSemanticsAudit,
    ClientSemanticsClass,
)
from fedact.domain.enums import DatasetSelector
from fedact.domain.records import SampleIdentifier

WeekIdentifier = NewType("WeekIdentifier", str)
CalendarMonthCell = NewType("CalendarMonthCell", str)
SupportCount = Annotated[int, Field(ge=0)]


@dataclass(frozen=True)
class EmberRawRecord:
    sample_hash: SampleIdentifier
    format_client: str
    collection_week: WeekIdentifier
    family: str | None


def conservative_timestamp_month(collection_week: WeekIdentifier) -> WeekIdentifier:
    return collection_week


def monthly_matching_cell(collection_week: WeekIdentifier) -> CalendarMonthCell:
    return CalendarMonthCell(collection_week[:7])


@dataclass(frozen=True)
class ControlMatchingLevel:
    weekly: bool


def choose_control_matching_level(
    weekly_support_per_side: SupportCount,
    minimum_support_per_class: PositiveInt,
    monthly_support_per_side: SupportCount,
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
    matched_week: str | None
    matched_month: str | None
    weekly_level: bool


def _matching_key(
    level: ControlMatchingLevel,
) -> Callable[[EmberRawRecord], CalendarMonthCell | WeekIdentifier]:
    if level.weekly:
        return lambda record: record.collection_week
    return lambda record: monthly_matching_cell(record.collection_week)


def match_ember_controls(
    malicious: tuple[EmberRawRecord, ...],
    controls: tuple[EmberRawRecord, ...],
    level: ControlMatchingLevel,
) -> tuple[EmberControlMatch, ...]:
    key = _matching_key(level)
    controls_by_cell: dict[str, list[EmberRawRecord]] = {}
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


def ember_client_semantics(observed_format_clients: tuple[str, ...]) -> ClientSemanticsAudit:
    return ClientSemanticsAudit(
        dataset=DatasetSelector.EMBER2024,
        source_field="format_client",
        classification=ClientSemanticsClass.DIAGNOSTIC_PARTITION,
        observed_values=observed_format_clients,
        supports_natural_federation_claim=False,
    )
