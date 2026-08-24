from __future__ import annotations

import re
from pathlib import Path

FORBIDDEN_ALIASES: frozenset[str] = frozenset(
    {"fedsira", "fabrid", "datp", "trajcert", "fedorbit", "fedcampaign"}
)
FORBIDDEN_ALIAS_PATTERN = re.compile(
    r"\b(" + "|".join(sorted(FORBIDDEN_ALIASES)) + r")\b", re.IGNORECASE
)


def alias_violations(repository_root: Path) -> list[str]:
    roots: list[Path] = [repository_root / "src", repository_root / "tests"]
    violations: list[str] = []
    for root in roots:
        for source_file in sorted(root.rglob("*.py")):
            if source_file.name == "test_canonical_vocabulary.py":
                continue
            relative = source_file.relative_to(repository_root).as_posix()
            for line_number, line in enumerate(
                source_file.read_text(encoding="utf-8").splitlines(), start=1
            ):
                match = FORBIDDEN_ALIAS_PATTERN.search(line)
                if match:
                    violations.append(
                        f"{relative}:{line_number}: forbidden alias '{match.group(0)}'"
                    )
    return violations


def test_sources_use_only_canonical_fedact_vocabulary(repository_root: Path) -> None:
    violations = alias_violations(repository_root)
    assert not violations, f"stale non-FedACT vocabulary found: {violations}"
