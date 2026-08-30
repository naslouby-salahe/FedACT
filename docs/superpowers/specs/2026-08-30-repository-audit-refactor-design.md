# Repository-Wide Audit and Refactor — Design

## Goal

Bring `src/fedact` into full compliance with `CLAUDE.md` and `docs/FedACT_Roadmap.md`: surgical refactor, not rewrite. Fix every mandatory quality-gate failure, close primitive/`Any`/enum gaps, verify roadmap dataset facts against real data, and confirm training/evaluation works end to end on real data.

## Scope

Datasets in scope: **LAMDA**, **EMBER2024** only (the only two named in the roadmap). Other datasets present under `data/raw` (CICIoMT2024, CIC_IOT_Dataset2023, CIC_IoT_DIAD_2024, Edge-IIoTset, Gotham2025, N-BaIoT, TON-IoT) are out of scope.

## Phases

Each phase fixes what it finds; no phase is audit-only.

1. **Baseline + gate fixes** — run ruff, strict pyright, semgrep, vulture, deptry, import-linter, pytest (unit/integration/architecture/smoke), coverage. Fix every failure, including pre-existing ones.
2. **Domain-contract refactor** — sweep for primitive-leak signatures, raw `dict`/`tuple`/`Any` contracts, missing enums, `canonical*` terminology, primitive obsession. Replace with typed domain models/enums/value objects at meaningful boundaries only (not blanket wrapping).
3. **Dataset/roadmap reconciliation** — inspect LAMDA and EMBER2024 under `data/raw` programmatically (schema, row counts, labels, clients, chronology, feature dimensions, missing/invalid values). Correct stale roadmap numbers with reproducible inspection results. Fix preprocessing where real schema contradicts current assumptions.
4. **Training/eval smoke** — lightweight real-data run through the training path for both datasets: local steps execute, aggregation receives typed updates, evaluation runs on correct split, metrics finite, artifacts serialize/deserialize, rerun deterministic.
5. **Hostile audit** — final pass against the CLAUDE.md 19-point checklist; close remaining gaps; rerun affected gates.

## Constraints

- No `canonical*` naming anywhere (forbidden per CLAUDE.md §14).
- No AI co-author attribution in any commit.
- Multiple commits, one per logical fix/phase-slice, pushed as work lands (not one giant commit at the end).
- No mass deletion — a file is deleted only when proven dead/duplicated/superseded/obsolete.
- Roadmap file itself is never deleted or broadly rewritten; only corrected dataset-fact numbers, cited to their inspection.
- Preserve CUDA/device-selection abstraction as-is unless it's actually broken.

## Out of scope

- Any dataset other than LAMDA/EMBER2024.
- Scientific protocol changes (algorithms, seeds, threat model, eligibility rules, statistical procedures) — only empirical dataset facts may be corrected.
- New features beyond what CLAUDE.md/roadmap already require.

## Verification

Phase-level Definition of Done matches CLAUDE.md §8: all mandatory gates green, no primitive/`Any` leakage, roadmap facts match real data, real-data training smoke passes, no TODO/placeholder residue, no `canonical` terms, git history clean of AI attribution.
