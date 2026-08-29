from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from fedact.domain.enums import EvidenceVerificationStatus
from fedact.domain.types import ArtifactName


@dataclass(frozen=True)
class EvidenceArtifactRecord:
    artifact: ArtifactName
    status: EvidenceVerificationStatus


def package_evidence_index(
    evidence_records: list[EvidenceArtifactRecord], output_file: Path
) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(r) for r in evidence_records]
    output_file.write_text(json.dumps(payload, indent=2) + chr(10), encoding="utf-8")
