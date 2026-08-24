from __future__ import annotations

from dataclasses import dataclass
from typing import NewType

from fedact.config.models import LamdaDatasetConfig
from fedact.datasets.records import (
    ClientSemanticsAudit,
    LabelDerivationRule,
    corpus_level_client_audit,
)
from fedact.domain.enums import DatasetSelector
from fedact.domain.records import SampleIdentifier
from fedact.domain.types import BinaryLabel, CalendarMonthString, FamilyName, SampleCount


@dataclass(frozen=True)
class LamdaRawRecord:
    sample_hash: SampleIdentifier
    year_month: CalendarMonthString
    label: BinaryLabel | None
    vt_count: SampleCount | None
    family: FamilyName | None


def label_derivation_rule(config: LamdaDatasetConfig) -> LabelDerivationRule:
    return LabelDerivationRule(
        benign_detection_count=config.labels.benign_detection_count,
        malware_minimum_detection_count=config.labels.malware_minimum_detection_count,
        discard_detection_counts=tuple(config.labels.discard_detection_counts),
    )


@dataclass(frozen=True)
class LabelAuditOutcome:
    binary_label: BinaryLabel | None


def audited_label(rule: LabelDerivationRule, record: LamdaRawRecord) -> LabelAuditOutcome:
    if record.label is not None and record.vt_count is not None:
        expected = _expected_label(rule, record.vt_count)
        if expected is None or expected != record.label:
            return LabelAuditOutcome(binary_label=None)
        return LabelAuditOutcome(binary_label=record.label)
    if record.label is not None:
        return LabelAuditOutcome(binary_label=record.label)
    if record.vt_count is not None:
        return LabelAuditOutcome(binary_label=_expected_label(rule, record.vt_count))
    return LabelAuditOutcome(binary_label=None)


def _expected_label(rule: LabelDerivationRule, vt_count: SampleCount) -> bool | None:
    if vt_count == rule.benign_detection_count:
        return False
    if vt_count >= rule.malware_minimum_detection_count:
        return True
    if vt_count in rule.discard_detection_counts:
        return None
    return None


@dataclass(frozen=True)
class LamdaControlMatch:
    malicious_sample_id: SampleIdentifier
    control_sample_id: SampleIdentifier
    calendar_month: CalendarMonthString


MaximumMatchesPerSample = NewType("MaximumMatchesPerSample", int)


@dataclass(frozen=True)
class MatchBudget:
    maximum_per_malicious: MaximumMatchesPerSample


def match_controls_by_calendar_month(
    malicious: tuple[LamdaRawRecord, ...],
    controls: tuple[LamdaRawRecord, ...],
    budget: MatchBudget,
) -> tuple[LamdaControlMatch, ...]:
    controls_by_month: dict[str, list[LamdaRawRecord]] = {}
    for control in controls:
        controls_by_month.setdefault(control.year_month, []).append(control)
    matches: list[LamdaControlMatch] = []
    used: set[SampleIdentifier] = set()
    for record in malicious:
        candidates = [
            control
            for control in controls_by_month.get(record.year_month, [])
            if control.sample_hash not in used
        ][: budget.maximum_per_malicious]
        for control in candidates:
            used.add(control.sample_hash)
            matches.append(
                LamdaControlMatch(
                    malicious_sample_id=record.sample_hash,
                    control_sample_id=control.sample_hash,
                    calendar_month=record.year_month,
                )
            )
    return tuple(matches)


def lamda_client_semantics() -> ClientSemanticsAudit:
    return corpus_level_client_audit(DatasetSelector.LAMDA)


@dataclass(frozen=True)
class OperatorEligibility:
    has_matching_raw_artifact: bool

    def is_eligible(self) -> bool:
        return self.has_matching_raw_artifact
