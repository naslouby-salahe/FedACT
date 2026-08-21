# M01 — Scientific Configuration, Repository, and Execution Contracts
> **Outcome:** Establish the authoritative configuration, typed repository contracts, artifact/provenance lifecycle, and generic dependency-aware execution substrate required by every scientific workflow.
## At a Glance
| Field | Value |
|---|---|
| Roadmap scope | `Front matter; §§1–2; Configuration YAML; §§19.1–19.3, 19.5, 34, 36–43 (global authority plus cross-cutting repository, artifact, runtime, and generic CLI portions)` |
| Requirement ownership | `931 implementation-bearing requirements; exact IDs in Coverage` |
| Upstream milestones | `None` |
| Implementation issues | `I01`, `I02`, `I03`, `I04`, `I05`, `I06` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | `I07` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every roadmap requirement owned by this milestone must be explicitly mapped to its future implementation issue(s) and objective verification evidence.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| Configuration YAML / linked definitions | Scientific configuration authority | REQ-1088–REQ-1255 | `I01` | Exact configuration schema/value/hash/fingerprint validation and forbidden-runtime-scientific-decision tests. |
| §§19.1–19.3, 19.5 | Workflow and artifact-boundary contracts | REQ-1282–REQ-1330, REQ-1394–REQ-1399, REQ-3298–REQ-3302 | `I02` | Workflow/artifact boundary schema tests, terminal-state fixtures, atomic completion and producer-ownership validation. |
| §34 | Provenance and reproducibility contracts | REQ-2014–REQ-2111 | `I03` | Required provenance-field, deterministic-execution, failure/recovery and reproducibility-invariant tests. |
| §36 | Repository, package, artifact and test architecture | REQ-2232–REQ-2424, REQ-2558–REQ-2565, REQ-2612–REQ-2647, REQ-2660–REQ-2730, REQ-2776–REQ-2778, REQ-2800–REQ-2828, REQ-2838, REQ-2850–REQ-2855, REQ-2859–REQ-2863, REQ-2866–REQ-2879 | `I04` | Repository component existence, dependency-boundary, static-typing, canonical-vocabulary and architecture test suite. |
| §§37, 42 | Generic workflow registry and CLI/runtime control | REQ-2880–REQ-2882, REQ-2936–REQ-2939, REQ-2952–REQ-2953, REQ-3086, REQ-3090, REQ-3095–REQ-3096, REQ-3111–REQ-3118, REQ-3122–REQ-3124, REQ-3128–REQ-3133, REQ-3137–REQ-3151, REQ-3162–REQ-3164, REQ-3174–REQ-3179, REQ-3201, REQ-3230–REQ-3236, REQ-3253–REQ-3263, REQ-3267–REQ-3285 | `I05` | CLI/runtime tests for registry, plan/doctor/run/status, dependency resolution, reuse/resume and prohibited flags. |
| §§38–41, 43.1 | Artifact lifecycle, reuse, invalidation and execution state | REQ-2955–REQ-3013, REQ-3015, REQ-3017, REQ-3019–REQ-3085, REQ-3202–REQ-3217, REQ-3292–REQ-3294 | `I06` | Artifact identity/completion/staleness/selective-invalidation/cache/logging and execution-state integration tests. |
| Scope / claim constraints | Global authority, terminology, primary estimand, novelty-credit exclusions, scope exclusions and claim boundaries (`NON_IMPLEMENTATION`; traceability only) | REQ-0001–REQ-0059 | — | Roadmap-to-inventory and claim/scope review confirms the constraints are preserved without creating fictitious implementation work. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation requirement must map to at least one real implementation issue before implementation begins; issue references remain `—` in this milestone-only phase.
- Every conditional requirement remains traceable and is implemented when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when implementation begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| — | No upstream milestone dependency. | `N/A` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Roadmap Coverage Inventory and authoritative configuration specification | Authoritative inputs | All owned requirements are `READY`; fixed configuration values are reproduced exactly and schema-valid. |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I01` — Implement Authoritative Scientific Configuration | Scientific configuration authority | `Configuration YAML / linked definitions` | 168 atomic requirements | None (foundational within this milestone chain) |
| 2 | `I02` — Implement Workflow and Artifact Boundary Contracts | Workflow and artifact-boundary contracts | `§§19.1–19.3, 19.5` | 60 atomic requirements | `I01` |
| 3 | `I03` — Implement Provenance and Reproducibility Contracts | Provenance and reproducibility contracts | `§34` | 98 atomic requirements | `I02` |
| 4 | `I04` — Establish Repository, Package, Artifact, and Test Architecture | Repository, package, artifact and test architecture | `§36` | 366 atomic requirements | `I03` |
| 5 | `I05` — Implement Generic Workflow Registry and CLI Runtime Control | Generic workflow registry and CLI/runtime control | `§§37, 42` | 92 atomic requirements | `I04` |
| 6 | `I06` — Implement Artifact Lifecycle, Reuse, Invalidation, and Execution State | Artifact lifecycle, reuse, invalidation and execution state | `§§38–41, 43.1` | 147 atomic requirements | `I05` |
| 7 | `I07` — Audit Scientific Configuration, Repository, and Execution Contracts | Independent milestone completion audit and `PASS`/`FAIL` gate | `Front matter; §§1–2; Configuration YAML; §§19.1–19.3, 19.5, 34, 36–43 (global authority plus cross-cutting repository, artifact, runtime, and generic CLI portions)`; Milestone `M01` completion contract: `Exit Criteria`, `Acceptance Evidence`, and `Milestone Audit`. | Audit / milestone-completion gate — no new primary requirements | `I06` |

### Issue Contract

Every milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Validated production configuration, typed domain/config contracts, and configuration hash semantics | `I01`, `I02`, `I03`, `I04`, `I05`, `I06` | Schema validation, exact fixed-value checks, and configuration-subset fingerprint tests | M02–M09 |
| Artifact identity, manifest, provenance, completion, dependency, storage, and lifecycle contracts | `I01`, `I02`, `I03`, `I04`, `I05`, `I06` | Atomic-completion, checksum, dependency-fingerprint, stale/invalidation, and provenance round-trip tests | M02–M09 |
| Generic workflow registry/runtime with plan, doctor, run/resume, status, reuse, cleanup, and scoped overwrite semantics | `I01`, `I02`, `I03`, `I04`, `I05`, `I06` | Architecture, unit, integration, E2E, crash/recovery, and forbidden-scientific-knob tests | M02–M09 |
| Roadmap-defined repository/output/results layout and architecture enforcement | `I01`, `I02`, `I03`, `I04`, `I05`, `I06` | Repository-structure, dependency-boundary, static-typing, vocabulary, and code-quality tests | M02–M09 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly referenced through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- The Roadmap Coverage Inventory and supplied milestone template are available and internally consistent for this milestone.
- All M01 implementation requirements are `READY`; no unresolved scientific decision is delegated to implementation.
- No upstream milestone dependency exists.
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- after issue decomposition, every mandatory implementation requirement is mapped to at least one real milestone issue and every mapped requirement has an explicit verification/evidence target;
- no blocking requirement is `UNMAPPED` or `AMBIGUOUS`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- The authoritative configuration loads and validates with every fixed scientific value preserved exactly.
- Artifact/provenance lifecycle operations enforce atomic completion, compatibility, selective invalidation, reusable-parent preservation, and non-reuse of incomplete/stale/invalid artifacts.
- The generic workflow registry/runtime and non-scientific CLI controls satisfy their exact command, reuse, resume, overwrite, status, and failure contracts.
- Repository architecture and architecture-quality tests enforce the roadmap-defined package, artifact, results, and test boundaries.
- every mandatory implementation requirement owned by this milestone is satisfied and every applicable conditional requirement is satisfied;
- every mapped implementation issue is closed;
- all required unit, integration, scientific, CLI/runtime, and validation procedures applicable to the milestone pass;
- all required deliverables, artifacts, interfaces, schemas, manifests, and provenance records are complete and valid;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS` with no unresolved blocking finding.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus future requirement-to-issue mapping | Every mandatory/applicable implementation requirement has exactly one primary milestone owner and completed evidence; traced `NON_IMPLEMENTATION` constraints are preserved. |
| Configuration authority | Schema validation, exact-value fixtures, configuration-hash and material-subset fingerprint tests | All fixed keys/values and configuration semantics match the inventory; invalid/missing values are rejected. |
| Artifact lifecycle | Lifecycle state-machine, atomic completion, crash injection, stale/invalidation and dependency-index tests | Only complete/valid compatible artifacts are reusable; stale/incomplete artifacts cannot enter active execution. |
| Provenance/reproducibility | Manifest round-trip, checksum, code/config/environment/seed identity, deterministic replay evidence | Required provenance fields are complete and sufficient to reconstruct scientific identity and compatibility. |
| Runtime/CLI | Unit/integration/E2E tests for doctor, plan, generic run/resume/status, scoped overwrite and failure isolation | Commands expose no prohibited scientific knobs and implement dependency-aware reuse/recompute semantics exactly. |
| Architecture | Repository structure, dependency-boundary, static typing, canonical vocabulary and code-quality checks | All roadmap-defined components/boundaries exist and architecture tests pass. |
| Deliverables / provenance | Required outputs, manifests, dependency identities and compatibility evidence | Outputs are complete, readable, schema-valid, provenance-complete, active, and non-stale. |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings. |

## Milestone Audit

**Audit issue:** `—`

**Audit status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability;
- closure of every mandatory implementation issue;
- completion and passing status of all required tests;
- completion and passing status of all required validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- M01 owns infrastructure and execution contracts, not downstream scientific workflow results.
- Scientific workflow-specific command names, experiment outcomes, model/data artifacts, and reporting products remain owned by later milestones.
- Global scientific authority, terminology, novelty exclusions, and claim boundaries are traced as non-implementation constraints and are not converted into implementation work.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues; detailed verification checklists belong in the future milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.


---

# M02 — Chronology-Safe Data, Representation, and Base Detector
> **Outcome:** Produce validated chronology-safe real/synthetic data products, cutoff/client/cohort partitions, and immutable cutoff-fixed representation and base-detector artifacts.
## At a Glance
| Field | Value |
|---|---|
| Roadmap scope | `§§6 (chronology/representation assumptions), 9–11, 36–37, 39, 42 (data, model, scoring, and preprocess portions)` |
| Requirement ownership | `346 implementation-bearing requirements; exact IDs in Coverage` |
| Upstream milestones | `M01` |
| Implementation issues | `I08`, `I09`, `I10`, `I11`, `I12`, `I13` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | `I14` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every roadmap requirement owned by this milestone must be explicitly mapped to its future implementation issue(s) and objective verification evidence.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §6 | Chronology and cutoff-fixed representation assumptions | REQ-0170–REQ-0172, REQ-0190–REQ-0192 | `I08` | Leakage fixtures, cutoff manifests, encoder-hash lock and exact failure-state tests. |
| §9 | Chronological information boundaries and cutoff scheduling | REQ-0488–REQ-0539 | `I09` | Half-open window, source-gap, horizon observability, no-shortening and later-real isolation tests. |
| §10 + linked definitions | Dataset acquisition, schema, eligibility and preprocessing | REQ-0540–REQ-0549, REQ-0551–REQ-0574, REQ-0576–REQ-0596, REQ-0598–REQ-0607, REQ-0611–REQ-0654, REQ-1272–REQ-1273 | `I10` | Schema/chronology manifests, observed-value validation, deterministic preprocessing/support/exclusion tests. |
| §11 | Cutoff-safe representation and detector training | REQ-0655–REQ-0701 | `I11` | Architecture/training/validation/retraining cadence/checkpoint-selection tests and immutable encoder provenance. |
| §36 | Dataset/model/training/scoring architecture and tests | REQ-2425–REQ-2483, REQ-2488–REQ-2497, REQ-2731–REQ-2744, REQ-2746–REQ-2749, REQ-2829, REQ-2839–REQ-2844 | `I12` | Roadmap-defined modules plus unit/integration/scientific chronology tests. |
| §§37, 39, 42 | Preprocess/shared-producer CLI and artifact ownership | REQ-2940–REQ-2945, REQ-2954, REQ-3014, REQ-3087–REQ-3089, REQ-3099–REQ-3100, REQ-3119–REQ-3121, REQ-3153–REQ-3154, REQ-3156–REQ-3161, REQ-3237–REQ-3241, REQ-3246–REQ-3252 | `I13` | `fedact preprocess` command, producer ownership, reuse, overwrite and selective-invalidation integration evidence. |
| Scope / claim constraints | Chronology/cutoff-fixed representation assumptions and dataset-role/eligibility boundaries (`NON_IMPLEMENTATION`; traceability only) | REQ-0169, REQ-0189, REQ-0550, REQ-0575, REQ-0597, REQ-0608–REQ-0610 | — | Roadmap-to-inventory and claim/scope review confirms the constraints are preserved without creating fictitious implementation work. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation requirement must map to at least one real implementation issue before implementation begins; issue references remain `—` in this milestone-only phase.
- Every conditional requirement remains traceable and is implemented when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when implementation begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M01 — Scientific Configuration, Repository, and Execution Contracts | Validated configuration, artifact/provenance contracts, repository boundaries, and preprocess-capable runtime interfaces | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Validated configuration and dataset/artifact path contracts | M01 | Configuration schema/hash and dependency-fingerprint validation. |
| Artifact manifest, provenance, completion, and storage interfaces | M01 | Atomic completion, integrity, and compatibility checks pass before produced artifacts are reusable. |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I08` — Enforce Chronology and Cutoff-Fixed Representation Assumptions | Chronology and cutoff-fixed representation assumptions | `§6` | 6 atomic requirements | `I07` |
| 2 | `I09` — Implement Chronological Information Boundaries and Cutoff Scheduling | Chronological information boundaries and cutoff scheduling | `§9` | 52 atomic requirements | `I08` |
| 3 | `I10` — Implement Dataset Acquisition, Validation, Eligibility, and Preprocessing | Dataset acquisition, schema, eligibility and preprocessing | `§10 + linked definitions` | 111 atomic requirements | `I09` |
| 4 | `I11` — Implement Cutoff-Safe Representation and Base Detector Training | Cutoff-safe representation and detector training | `§11` | 47 atomic requirements | `I10` |
| 5 | `I12` — Implement Data, Model, Training, and Scoring Architecture | Dataset/model/training/scoring architecture and tests | `§36` | 94 atomic requirements | `I11` |
| 6 | `I13` — Implement Preprocess CLI and Shared Producer Ownership | Preprocess/shared-producer CLI and artifact ownership | `§§37, 39, 42` | 36 atomic requirements | `I12` |
| 7 | `I14` — Audit Chronology-Safe Data, Representation, and Base Detector | Independent milestone completion audit and `PASS`/`FAIL` gate | `§§6 (chronology/representation assumptions), 9–11, 36–37, 39, 42 (data, model, scoring, and preprocess portions)`; Milestone `M02` completion contract: `Exit Criteria`, `Acceptance Evidence`, and `Milestone Audit`. | Audit / milestone-completion gate — no new primary requirements | `I13` |

### Issue Contract

Every milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Raw-schema/chronology inventories and canonical prepared LAMDA/EMBER2024/synthetic data products | `I08`, `I09`, `I10`, `I11`, `I12`, `I13` | Dataset schema, checksum, chronology, duplicate/malformed/missing-record and observed-value-rule validation | M03–M09 |
| Cutoff, split, client, cohort, eligibility, exclusion, and preprocessing manifests | `I08`, `I09`, `I10`, `I11`, `I12`, `I13` | Leakage audit, half-open interval checks, source-gap handling, support eligibility, and deterministic cutoff enumeration | M03–M09 |
| Cutoff-fixed representation and base-detector checkpoints plus reusable encodings/scores | `I08`, `I09`, `I10`, `I11`, `I12`, `I13` | Training/validation semantics, encoder-hash lock, deterministic scoring, checkpoint/sample identity, and leakage tests | M03–M09 |
| `fedact preprocess` producer outputs and preprocess ownership manifests | `I08`, `I09`, `I10`, `I11`, `I12`, `I13` | CLI integration validates corpus selection, reuse/overwrite, owned artifacts, and downstream invalidation | M03–M09 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly referenced through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M01 is complete with audit `PASS`.
- Validated configuration, artifact/provenance interfaces, and repository paths required for dataset/model products are available.
- Acquired corpus identities required by the roadmap are available to the applicable loader; missing source semantics narrow eligibility rather than being synthesized.
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- after issue decomposition, every mandatory implementation requirement is mapped to at least one real milestone issue and every mapped requirement has an explicit verification/evidence target;
- no blocking requirement is `UNMAPPED` or `AMBIGUOUS`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- All dataset loaders emit schema/chronology manifests before scientific transformation and enforce the complete chronological information boundary.
- Prepared data, cutoffs, splits, clients, cohorts, controls, and exclusions are deterministic and provenance-complete.
- Representation and base-detector training use cutoff-safe data only, and the selected encoder remains immutable within each cutoff experiment.
- Reusable encodings/scores and preprocess-owned artifacts pass completeness, determinism, identity, and leakage validation.
- every mandatory implementation requirement owned by this milestone is satisfied and every applicable conditional requirement is satisfied;
- every mapped implementation issue is closed;
- all required unit, integration, scientific, CLI/runtime, and validation procedures applicable to the milestone pass;
- all required deliverables, artifacts, interfaces, schemas, manifests, and provenance records are complete and valid;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS` with no unresolved blocking finding.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus future requirement-to-issue mapping | Every mandatory/applicable implementation requirement has exactly one primary milestone owner and completed evidence; traced `NON_IMPLEMENTATION` constraints are preserved. |
| Chronology | Cutoff manifests, leakage tests, source-gap fixtures, half-open interval and later-real isolation checks | No post-cutoff information influences fitting, calibration inputs, cohorts, operators, actions, hardening, or baselines. |
| Dataset preparation | Schema/data-quality manifests and dataset-validation tests on acquired data | Observed source fields/counts/semantics are recorded; unsupported/missing semantics cause the roadmap-defined eligibility outcome. |
| Training | Checkpoint manifests, validation-split evidence, deterministic seed records and encoder-hash lock | Representation/base detector satisfy §11 architecture/training/selection rules with immutable cutoff identity. |
| Scoring | Encoding/scoring completeness and deterministic replay tests | Same checkpoint/sample identity yields reusable deterministic encodings/scores with no leakage. |
| CLI producer | `fedact preprocess` integration tests and artifact ownership manifests | Preprocess creates only its declared artifacts, reuses compatible work, and selectively invalidates affected descendants on overwrite. |
| Deliverables / provenance | Required outputs, manifests, dependency identities and compatibility evidence | Outputs are complete, readable, schema-valid, provenance-complete, active, and non-stale. |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings. |

## Milestone Audit

**Audit issue:** `—`

**Audit status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability;
- closure of every mandatory implementation issue;
- completion and passing status of all required tests;
- completion and passing status of all required validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- M02 does not implement domain mutation operators, FedACT identification, comparator parity, or prospective evaluation.
- Retrospective annotations may not define confirmatory operational cohorts; unavailable semantics are not synthesized.
- Later-real observations remain evaluation-only and cannot alter earlier cutoff artifacts.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues; detailed verification checklists belong in the future milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.


---

# M03 — Domain-Valid Action Operator Library
> **Outcome:** Provide the complete provenance-locked PE/APK operator library, action-displacement construction, and multi-layer domain-validity gates required before FedACT can certify defensive actions.
## At a Glance
| Field | Value |
|---|---|
| Roadmap scope | `§§6 (action/operator assumptions), 12, 36 (operator portions)` |
| Requirement ownership | `124 implementation-bearing requirements; exact IDs in Coverage` |
| Upstream milestones | `M01, M02` |
| Implementation issues | `I15`, `I16`, `I17`, `I18`, `I19` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | `I20` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every roadmap requirement owned by this milestone must be explicitly mapped to its future implementation issue(s) and objective verification evidence.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §6 | Action-validity and operator-coverage assumptions | REQ-0194–REQ-0196, REQ-0218–REQ-0219 | `I15` | Operator validity and pre-cutoff coverage audits plus exact invalid/unavailable failure semantics. |
| §§12.1–12.2 | Operator contracts and action displacements | REQ-0702–REQ-0726 | `I16` | Typed operator records, deterministic enumeration, displacement and zero-floor analytical/unit fixtures. |
| §§12.3–12.4 | PE and APK operator implementations | REQ-0727–REQ-0767 | `I17` | Pinned parser/build/sandbox/emulator execution evidence for every required family/parameter contract. |
| §§12.5–12.7 | Operator validation, failure semantics and provenance | REQ-0768–REQ-0803 | `I18` | Structural, smoke, maliciousness, behavior-preservation, coverage and provenance validation. |
| §36 | Operator architecture and tests | REQ-2498–REQ-2509, REQ-2750–REQ-2754 | `I19` | Roadmap-defined operator modules and unit tests pass. |
| Scope / claim constraints | Action-validity and operator-coverage assumptions (`NON_IMPLEMENTATION`; traceability only) | REQ-0193, REQ-0217 | — | Roadmap-to-inventory and claim/scope review confirms the constraints are preserved without creating fictitious implementation work. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation requirement must map to at least one real implementation issue before implementation begins; issue references remain `—` in this milestone-only phase.
- Every conditional requirement remains traceable and is implemented when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when implementation begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M01 — Scientific Configuration, Repository, and Execution Contracts | Operator configuration, artifact/provenance contracts, dependency identity, and repository boundaries | `Complete + audit PASS` |
| M02 — Chronology-Safe Data, Representation, and Base Detector | Cutoff-safe samples, immutable encoder checkpoints/embeddings, and dataset-specific input semantics | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Cutoff-safe samples and immutable `E_T` checkpoint identity | M02 | Sample/cutoff/checkpoint provenance and leakage checks pass. |
| Operator validation/toolchain configuration and provenance schema | M01 | Pinned executable/tool identities and required validator parameters are recorded before use. |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I15` — Enforce Action Validity and Operator Coverage Assumptions | Action-validity and operator-coverage assumptions | `§6` | 5 atomic requirements | `I07`, `I14` |
| 2 | `I16` — Implement Operator Contracts and Action Displacements | Operator contracts and action displacements | `§§12.1–12.2` | 25 atomic requirements | `I15` |
| 3 | `I17` — Implement PE and APK Action Operators | PE and APK operator implementations | `§§12.3–12.4` | 41 atomic requirements | `I16` |
| 4 | `I18` — Implement Operator Validation, Failure Semantics, and Provenance | Operator validation, failure semantics and provenance | `§§12.5–12.7` | 36 atomic requirements | `I17` |
| 5 | `I19` — Implement Operator Architecture and Verification | Operator architecture and tests | `§36` | 17 atomic requirements | `I18` |
| 6 | `I20` — Audit Domain-Valid Action Operator Library | Independent milestone completion audit and `PASS`/`FAIL` gate | `§§6 (action/operator assumptions), 12, 36 (operator portions)`; Milestone `M03` completion contract: `Exit Criteria`, `Acceptance Evidence`, and `Milestone Audit`. | Audit / milestone-completion gate — no new primary requirements | `I19` |

### Issue Contract

Every milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Typed operator definitions, canonical parameters, and valid candidate enumeration | `I15`, `I16`, `I17`, `I18`, `I19` | Unit tests for operator records, deterministic enumeration, composition limits, and nondegenerate displacement semantics | M04–M09 |
| PE operator implementations and pinned validation toolchain integration | `I15`, `I16`, `I17`, `I18`, `I19` | Structural parsing, execution-smoke, maliciousness-preservation, behavior-preservation, timeout and failure-code tests | M04–M09 |
| APK operator implementations and pinned Android validation toolchain integration | `I15`, `I16`, `I17`, `I18`, `I19` | APK structural, emulator/smoke, maliciousness-preservation, behavior-preservation and provenance tests | M04–M09 |
| Validated action displacements and pre-cutoff operator coverage/validity evidence | `I15`, `I16`, `I17`, `I18`, `I19` | Zero-displacement rejection, validity audit, operator-library coverage audit and exact failure-state verification | M04–M09 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly referenced through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M01 and M02 are complete with audit `PASS`.
- Cutoff-safe samples and immutable representation checkpoints exist for action-displacement construction.
- Required operator toolchain/executable identities are available or the roadmap-defined unavailable/invalid outcome is used.
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- after issue decomposition, every mandatory implementation requirement is mapped to at least one real milestone issue and every mapped requirement has an explicit verification/evidence target;
- no blocking requirement is `UNMAPPED` or `AMBIGUOUS`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- Every roadmap-defined PE/APK operator family and parameter contract is implemented without later-real tuning.
- Every generated candidate passes the required structural, execution-smoke, maliciousness-preservation, and behavior-preservation layers before statistical use.
- Degenerate or invalid transformations are rejected with exact roadmap states/reasons and cannot be certified.
- Operator provenance, pre-cutoff operator-library coverage diagnostics, and deterministic action-displacement artifacts are complete and reusable; later-real operator-coverage validation remains a downstream M07 gate.
- every mandatory implementation requirement owned by this milestone is satisfied and every applicable conditional requirement is satisfied;
- every mapped implementation issue is closed;
- all required unit, integration, scientific, CLI/runtime, and validation procedures applicable to the milestone pass;
- all required deliverables, artifacts, interfaces, schemas, manifests, and provenance records are complete and valid;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS` with no unresolved blocking finding.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus future requirement-to-issue mapping | Every mandatory/applicable implementation requirement has exactly one primary milestone owner and completed evidence; traced `NON_IMPLEMENTATION` constraints are preserved. |
| Operator contracts | Typed-record and enumeration tests | Canonical names/parameters/composition rules and deterministic ordering match §12. |
| PE validity | Pinned-tool parsing, sandbox execution, maliciousness and behavior-preservation evidence | Only transformations passing all required PE validity layers are eligible. |
| APK validity | Pinned-tool/emulator structural, smoke, maliciousness and behavior evidence | Only transformations passing all required APK validity layers are eligible. |
| Action displacement | Analytical/fixture checks for `d_o(x)`/normalized direction and zero-displacement rejection | Displacements use the immutable cutoff encoder and degenerate actions are excluded deterministically. |
| Failure semantics | Negative-path tests for invalid/unavailable operator conditions | Exact failure/missingness outcomes are recorded and excluded from confirmatory evidence as specified. |
| Deliverables / provenance | Required outputs, manifests, dependency identities and compatibility evidence | Outputs are complete, readable, schema-valid, provenance-complete, active, and non-stale. |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings. |

## Milestone Audit

**Audit issue:** `—`

**Audit status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability;
- closure of every mandatory implementation issue;
- completion and passing status of all required tests;
- completion and passing status of all required validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- M03 establishes domain validity and the pre-cutoff operator-library coverage audit; statistical certification remains a separate M04 requirement, and later-real operator-coverage validation remains a downstream M07 requirement.
- Operator families, parameter grids, validators, and versions may not be selected using later-real outcomes.
- No invalid transformation may be rescued by statistical support.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues; detailed verification checklists belong in the future milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.


---

# M04 — FedACT Identification, Certification, and Mathematical Verification
> **Outcome:** Implement the complete FedACT client/server identification and certification engine, including finite-sample uncertainty, temporal set propagation, action support, abstention/hardening semantics, and verified mathematical/numerical contracts.
## At a Glance
| Field | Value |
|---|---|
| Roadmap scope | `§§4–8, 13, 19.4, 20, 36–37, 42 (FedACT and math-verification portions)` |
| Requirement ownership | `471 implementation-bearing requirements; exact IDs in Coverage` |
| Upstream milestones | `M01, M02, M03` |
| Implementation issues | `I21`, `I22`, `I23`, `I24`, `I25`, `I26` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | `I27` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every roadmap requirement owned by this milestone must be explicitly mapped to its future implementation issue(s) and objective verification evidence.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §4 | Primary estimand, feasible-set, propagation and certificate mathematics | REQ-0100–REQ-0108, REQ-0110–REQ-0137, REQ-0139–REQ-0141 | `I21` | Analytical identities and known-truth fixtures agree within locked numerical tolerances. |
| §5 | Deterministic mechanism and solver validation obligations | REQ-0143–REQ-0145, REQ-0154–REQ-0155 | `I22` | Control-quality, support-solver and monotonicity tests produce required evidence. |
| §§6–7 + linked definitions | Assumptions, finite-sample uncertainty and theoretical guarantees | REQ-0174–REQ-0176, REQ-0178–REQ-0180, REQ-0182–REQ-0184, REQ-0186–REQ-0188, REQ-0198–REQ-0200, REQ-0202–REQ-0204, REQ-0206–REQ-0208, REQ-0210–REQ-0212, REQ-0214–REQ-0216, REQ-0222–REQ-0224, REQ-0230–REQ-0237, REQ-0240–REQ-0245, REQ-0247–REQ-0250, REQ-0252–REQ-0257, REQ-0259, REQ-0261–REQ-0263, REQ-0265–REQ-0268, REQ-0270–REQ-0276, REQ-0278–REQ-0283, REQ-0285–REQ-0288, REQ-0290–REQ-0292, REQ-0294–REQ-0296, REQ-0298–REQ-0300, REQ-0302–REQ-0309, REQ-0311, REQ-1256–REQ-1261, REQ-1276–REQ-1279 | `I23` | Bootstrap/subspace/coverage/conditioning/non-identification fixtures and proof obligations match executable estimators. |
| §§8, 13 | Client/server FedACT algorithm, feasible sets, certification and hardening | REQ-0312–REQ-0360, REQ-0362–REQ-0414, REQ-0416–REQ-0431, REQ-0433–REQ-0487, REQ-0804–REQ-0831, REQ-0836–REQ-0837, REQ-3297 | `I24` | End-to-end client/server scientific artifacts plus exact gate/abstention/hardening tests. |
| §§19.4, 20 | Mathematical and numerical verification workflow | REQ-1331–REQ-1354, REQ-1401–REQ-1403, REQ-1405, REQ-1407–REQ-1434 | `I25` | All §20 analytical solver/set/action verification outputs complete and pass. |
| §§36–37, 42 | FedACT/math-verification architecture, tests and CLI | REQ-2486–REQ-2487, REQ-2510–REQ-2535, REQ-2566–REQ-2567, REQ-2745, REQ-2755–REQ-2766, REQ-2779, REQ-2830–REQ-2834, REQ-2846–REQ-2848, REQ-2883–REQ-2887, REQ-3101, REQ-3169 | `I26` | FedACT modules, scientific tests, integration tests and `run math-verification` command evidence. |
| Scope / claim constraints | Mechanism ordering, core assumptions, theorem classes, non-identification limits and federation-claim boundaries (`NON_IMPLEMENTATION`; traceability only) | REQ-0142, REQ-0148, REQ-0152, REQ-0156, REQ-0173, REQ-0177, REQ-0181, REQ-0185, REQ-0197, REQ-0201, REQ-0205, REQ-0209, REQ-0213, REQ-0221, REQ-0225–REQ-0229, REQ-0238–REQ-0239, REQ-0246, REQ-0251, REQ-0258, REQ-0264, REQ-0269, REQ-0277, REQ-0284, REQ-0289, REQ-0293, REQ-0297, REQ-0301, REQ-0832–REQ-0835 | — | Roadmap-to-inventory and claim/scope review confirms the constraints are preserved without creating fictitious implementation work. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation requirement must map to at least one real implementation issue before implementation begins; issue references remain `—` in this milestone-only phase.
- Every conditional requirement remains traceable and is implemented when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when implementation begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M01 — Scientific Configuration, Repository, and Execution Contracts | Fixed scientific/numerical configuration, artifact/provenance contracts, and solver/runtime interfaces | `Complete + audit PASS` |
| M02 — Chronology-Safe Data, Representation, and Base Detector | Cutoff-safe transitions, controls, immutable representation and base-detector artifacts | `Complete + audit PASS` |
| M03 — Domain-Valid Action Operator Library | Validated nondegenerate action candidates and displacement directions with provenance | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Cutoff/client/cohort transition and control summaries | M02 | Chronology, support, split and checkpoint identity validation. |
| Validated operator candidates/displacements | M03 | All operator-validity layers pass; encoder identity matches active cutoff. |
| Scientific/numerical configuration and solver tolerances | M01 | Schema/hash compatibility and exact configured values. |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I21` — Implement FedACT Estimand, Feasible-Set, Propagation, and Certificate Mathematics | Primary estimand, feasible-set, propagation and certificate mathematics | `§4` | 40 atomic requirements | `I07`, `I14`, `I20` |
| 2 | `I22` — Verify Deterministic Mechanism and Solver Invariants | Deterministic mechanism and solver validation obligations | `§5` | 5 atomic requirements | `I21` |
| 3 | `I23` — Implement Finite-Sample Uncertainty and Theoretical Guarantee Contracts | Assumptions, finite-sample uncertainty and theoretical guarantees | `§§6–7 + linked definitions` | 107 atomic requirements | `I22` |
| 4 | `I24` — Implement the End-to-End FedACT Client and Server Algorithm | Client/server FedACT algorithm, feasible sets, certification and hardening | `§§8, 13` | 204 atomic requirements | `I23` |
| 5 | `I25` — Implement Mathematical and Numerical Verification Workflow | Mathematical and numerical verification workflow | `§§19.4, 20` | 56 atomic requirements | `I24` |
| 6 | `I26` — Implement FedACT Verification Architecture, Tests, and CLI | FedACT/math-verification architecture, tests and CLI | `§§36–37, 42` | 59 atomic requirements | `I25` |
| 7 | `I27` — Audit FedACT Identification, Certification, and Mathematical Verification | Independent milestone completion audit and `PASS`/`FAIL` gate | `§§4–8, 13, 19.4, 20, 36–37, 42 (FedACT and math-verification portions)`; Milestone `M04` completion contract: `Exit Criteria`, `Acceptance Evidence`, and `Milestone Audit`. | Audit / milestone-completion gate — no new primary requirements | `I26` |

### Issue Contract

Every milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Client constraint engine: malicious/control transitions, nuisance rank/projectors, covariance and uncertainty components, quality gates and transmitted summaries | `I21`, `I22`, `I23`, `I24`, `I25`, `I26` | Analytical fixtures, bootstrap determinism, eigengap/stability, held-out reconstruction and exact abstention-state tests | M05–M09 |
| Server feasible-set engine, historical plausibility construction, infeasibility diagnostics, Chebyshev centers and temporal propagation | `I21`, `I22`, `I23`, `I24`, `I25`, `I26` | SOCP/support/center/diameter analytical validation, non-circularity tests, infeasibility preservation and provenance checks | M05–M09 |
| Action support intervals, certification/ambiguity/abstention decisions, leave-one-client-out stability, challenge selection and hardening algorithm | `I21`, `I22`, `I23`, `I24`, `I25`, `I26` | Support-solver parity, monotonicity, deterministic tie rules, certificate-state and hardening-loss/checkpoint eligibility tests | M05–M09 |
| Mathematical verification workflow and proof/numerical evidence | `I21`, `I22`, `I23`, `I24`, `I25`, `I26` | Exact identified-set, functional-identifiability, conditioning, monotonicity, synchronized-nuisance, solver, center, diameter, degeneracy and infeasibility checks | M05–M09 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly referenced through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M01–M03 are complete with audit `PASS`.
- All consumed data/checkpoint/operator artifacts are compatible with the active cutoff and configuration.
- No required scientific/numerical quantity is left unspecified; all implementation-bearing M04 requirements are `READY`.
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- after issue decomposition, every mandatory implementation requirement is mapped to at least one real milestone issue and every mapped requirement has an explicit verification/evidence target;
- no blocking requirement is `UNMAPPED` or `AMBIGUOUS`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- The primary estimand remains the feasible transition set and action-support interval; point quantities remain diagnostics/comparators only.
- All client uncertainty components, quality gates, failure states, server set construction, propagation, support solves, certification, abstention and hardening semantics match the inventory exactly.
- Mathematical/numerical verification passes every analytical known-truth case and blocks downstream use on unresolved solver/set errors.
- All M04 outputs and provenance are complete, finite where required, and compatible for synthetic and real downstream workflows.
- every mandatory implementation requirement owned by this milestone is satisfied and every applicable conditional requirement is satisfied;
- every mapped implementation issue is closed;
- all required unit, integration, scientific, CLI/runtime, and validation procedures applicable to the milestone pass;
- all required deliverables, artifacts, interfaces, schemas, manifests, and provenance records are complete and valid;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS` with no unresolved blocking finding.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus future requirement-to-issue mapping | Every mandatory/applicable implementation requirement has exactly one primary milestone owner and completed evidence; traced `NON_IMPLEMENTATION` constraints are preserved. |
| Mathematics | Self-contained derivations plus analytical toy-system fixtures | Roadmap identities/conditions hold within locked tolerances; theorem verification uses only executable estimators/constants. |
| Client constraints | Bootstrap/eigengap/control-reconstruction/private-allowance fixtures and negative-path tests | Usable clients satisfy every quality gate; exact abstention/failure codes occur when gates fail. |
| Feasible sets and solvers | Support, feasibility, Chebyshev-center, diameter and monotonicity analytical tests | Numerical solutions match analytical cases; infeasible sets remain infeasible and diagnostic inflation is never substituted. |
| Certification | Action-state/certificate fixtures, leave-one-client-out reconstruction and wide-forecast-set tests | Certification uses exact alignment/width/validity gates and required stability/abstention semantics. |
| Hardening | Loss/objective/checkpoint-selection and clean-cost eligibility tests | Only certified valid challenges are used; encoder is frozen and invalid candidates cannot become selected checkpoints. |
| Math workflow | `fedact run math-verification` completion artifact and solver diagnostics | Workflow completes with all mandatory verification results passing before synthetic theory validation. |
| Deliverables / provenance | Required outputs, manifests, dependency identities and compatibility evidence | Outputs are complete, readable, schema-valid, provenance-complete, active, and non-stale. |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings. |

## Milestone Audit

**Audit issue:** `—`

**Audit status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability;
- closure of every mandatory implementation issue;
- completion and passing status of all required tests;
- completion and passing status of all required validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- M04 does not claim full transition identification when only action functionals are identified.
- Synchronized residual nuisance outside all controls remains a fundamental non-identification boundary.
- Robust sensitivity may diagnose tail dependence but may not silently replace the primary estimator.
- A single usable client may support local mechanism evidence but never a federation claim.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues; detailed verification checklists belong in the future milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.


---

# M05 — Synthetic Mechanism and Geometry Validation
> **Outcome:** Validate FedACT under known truth through the locked synthetic generator, smoke checks, geometry/uncertainty sweeps, and mechanism-level falsification tests before real-data confirmation.
## At a Glance
| Field | Value |
|---|---|
| Roadmap scope | `§§3, 5, 19.4, 21–22, 36–37, 39, 42 (known-truth mechanism and synthetic portions)` |
| Requirement ownership | `197 implementation-bearing requirements; exact IDs in Coverage` |
| Upstream milestones | `M04` |
| Implementation issues | `I28`, `I29`, `I30`, `I31` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | `I32` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every roadmap requirement owned by this milestone must be explicitly mapped to its future implementation issue(s) and objective verification evidence.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §5 | Known-truth mechanism evidence | REQ-0146–REQ-0147, REQ-0149–REQ-0151, REQ-0153 | `I28` | Locked known-truth experiments for constraint validity, set contraction and action-specific geometry. |
| §21 | Synthetic generator, geometry and smoke validation | REQ-1435–REQ-1443, REQ-1445–REQ-1452, REQ-1454–REQ-1472, REQ-1474–REQ-1517 | `I29` | Generator invariants, deterministic replay and smoke manifest. |
| §22 | Synthetic theory and geometry sweep program | REQ-1518–REQ-1581, REQ-1583–REQ-1598 | `I30` | Complete locked sweep manifests, source data, metrics, diagnostics and falsification outcomes. |
| §§19.4, 36–37, 39, 42 | Synthetic workflow architecture, artifacts and CLI | REQ-1355–REQ-1360, REQ-2568–REQ-2569, REQ-2780, REQ-2864–REQ-2865, REQ-2888–REQ-2892, REQ-2933, REQ-3016, REQ-3091, REQ-3102, REQ-3125–REQ-3127, REQ-3165–REQ-3168, REQ-3170, REQ-3264–REQ-3266 | `I31` | Synthetic workflow modules/tests plus smoke/synthetic-geometry command and artifact contracts. |
| Scope / claim constraints | Known-truth feasible-set, action-identification, action-specific-information hypotheses and synthetic scope boundary (`NON_IMPLEMENTATION`; traceability only) | REQ-0060–REQ-0066, REQ-0073–REQ-0075, REQ-1582 | — | Roadmap-to-inventory and claim/scope review confirms the constraints are preserved without creating fictitious implementation work. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation requirement must map to at least one real implementation issue before implementation begins; issue references remain `—` in this milestone-only phase.
- Every conditional requirement remains traceable and is implemented when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when implementation begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M04 — FedACT Identification, Certification, and Mathematical Verification | Verified solver, FedACT set/certificate engine, mathematical identities, and executable uncertainty semantics | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Verified FedACT math/solver artifacts | M04 | All mathematical/numerical verification completion gates pass. |
| Synthetic configuration/seeds and artifact contracts | M01 | Configuration/hash/seed identity and provenance validation. |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I29` — Implement Synthetic Generator and Smoke Validation | Synthetic generator, geometry and smoke validation | `§21` | 80 atomic requirements | `I27` |
| 2 | `I28` — Validate Known-Truth FedACT Mechanism Evidence | Known-truth mechanism evidence | `§5` | 6 atomic requirements | `I27`, `I29` |
| 3 | `I30` — Execute Synthetic Theory and Geometry Sweeps | Synthetic theory and geometry sweep program | `§22` | 80 atomic requirements | `I28` |
| 4 | `I31` — Implement Synthetic Workflow Architecture, Artifacts, and CLI | Synthetic workflow architecture, artifacts and CLI | `§§19.4, 36–37, 39, 42` | 31 atomic requirements | `I30` |
| 5 | `I32` — Audit Synthetic Mechanism and Geometry Validation | Independent milestone completion audit and `PASS`/`FAIL` gate | `§§3, 5, 19.4, 21–22, 36–37, 39, 42 (known-truth mechanism and synthetic portions)`; Milestone `M05` completion contract: `Exit Criteria`, `Acceptance Evidence`, and `Milestone Audit`. | Audit / milestone-completion gate — no new primary requirements | `I31` |

### Issue Contract

Every milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Deterministic 64-dimensional synthetic generator with nuisance geometry, controls, private/synchronized residuals, sampling noise and action geometry | `I28`, `I29`, `I30`, `I31` | Generator smoke validation, orthonormality/intersection checks, deterministic replay and exact default/sweep validation | M06–M09 |
| Complete synthetic theory/geometry sweep source data, metrics and diagnostics | `I28`, `I29`, `I30`, `I31` | Locked grid/seed manifests, matched-factor controls, known-truth coverage and numerical consistency checks | M06–M09 |
| Known-truth evidence for controls→constraints→sets→action intervals and information/complementarity behavior | `I28`, `I29`, `I30`, `I31` | Coverage, width, monotonicity, action-orientation, redundant/complementary and conditioning analyses | M06–M09 |
| Synthetic workflow completion and CLI artifacts | `I28`, `I29`, `I30`, `I31` | `fedact smoke` and `fedact run synthetic-geometry` manifests with dependency-aware reuse and terminal scientific outcomes | M06–M09 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly referenced through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M04 is complete with audit `PASS`.
- Synthetic configuration, seeds, generator identities and verified solver/FedACT artifacts are available and compatible.
- The smoke workflow can execute without real-data or later-real dependencies.
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- after issue decomposition, every mandatory implementation requirement is mapped to at least one real milestone issue and every mapped requirement has an explicit verification/evidence target;
- no blocking requirement is `UNMAPPED` or `AMBIGUOUS`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- Synthetic smoke validation passes all generator invariants and deterministic replay checks.
- Every mandatory §22 sweep executes with only its named factor varied and produces complete known-truth source data/metrics/diagnostics.
- Feasible-set calibration, action-specific identification, complementarity versus redundancy, sample-size/conditioning behavior and declared mechanism checks are objectively evaluated.
- Null/adverse synthetic outcomes are preserved as scientific outcomes rather than triggering post hoc retuning.
- every mandatory implementation requirement owned by this milestone is satisfied and every applicable conditional requirement is satisfied;
- every mapped implementation issue is closed;
- all required unit, integration, scientific, CLI/runtime, and validation procedures applicable to the milestone pass;
- all required deliverables, artifacts, interfaces, schemas, manifests, and provenance records are complete and valid;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS` with no unresolved blocking finding.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus future requirement-to-issue mapping | Every mandatory/applicable implementation requirement has exactly one primary milestone owner and completed evidence; traced `NON_IMPLEMENTATION` constraints are preserved. |
| Generator correctness | Smoke manifest, orthogonality/intersection checks, sample/noise invariant tests and deterministic replay | Generated states exactly satisfy configured geometry and known-truth construction rules. |
| Coverage/calibration | Known-truth set/action coverage with Monte Carlo uncertainty | Observed coverage is compared with the selected nominal level under the prespecified acceptance rule. |
| Geometry mechanism | Principal-angle, common-nullspace, action-rotation, spectral-conditioning and matched redundant/complementary sweeps | Outputs show the measured set/action consequences or record falsification without redefining the hypothesis. |
| Finite-sample behavior | Control/malicious sample-size and amplitude-mismatch sweeps | Reducible uncertainty and structural residual behavior are reported from locked conditions. |
| Workflow execution | Smoke and synthetic-geometry manifests, metrics and diagnostics | All required cells/seeds reach valid terminal scientific states with complete provenance. |
| Deliverables / provenance | Required outputs, manifests, dependency identities and compatibility evidence | Outputs are complete, readable, schema-valid, provenance-complete, active, and non-stale. |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings. |

## Milestone Audit

**Audit issue:** `—`

**Audit status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability;
- closure of every mandatory implementation issue;
- completion and passing status of all required tests;
- completion and passing status of all required validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- Synthetic federation establishes mathematical/mechanism behavior but does not establish real organizational complementarity.
- M05 does not use later-real outcomes and does not alter real-data calibration or claim thresholds.
- Feasible-set, action-identification, and action-specific geometry hypotheses are evaluated as prespecified; adverse results remain valid evidence.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues; detailed verification checklists belong in the future milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.


---

# M06 — Real-Data Feasibility, Baselines, Metrics, and Nested Calibration
> **Outcome:** Establish real-data eligibility, comparator parity, full evaluation/statistical primitives, and leakage-safe nested pre-cutoff calibration required by confirmatory prospective workflows.
## At a Glance
| Field | Value |
|---|---|
| Roadmap scope | `§§14, 16–17, 19.4, 23–25, 36–37 (feasibility, baseline, evaluation, statistics, and calibration portions)` |
| Requirement ownership | `395 implementation-bearing requirements; exact IDs in Coverage` |
| Upstream milestones | `M05` |
| Implementation issues | `I33`, `I34`, `I35`, `I36`, `I37`, `I38` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | `I39` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every roadmap requirement owned by this milestone must be explicitly mapped to its future implementation issue(s) and objective verification evidence.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §§14, 24 + linked definitions | Comparator implementation, fairness and parity validation | REQ-0838–REQ-0843, REQ-0845, REQ-0847, REQ-0849, REQ-0851, REQ-0853, REQ-0855, REQ-0857, REQ-0859, REQ-0861, REQ-0863, REQ-0865, REQ-0867, REQ-0869–REQ-0915, REQ-1280–REQ-1281, REQ-1633–REQ-1650 | `I33` | Comparator identity/provenance, fairness checks and analytical/synthetic/chronological parity artifacts. |
| §§16–17 + linked definitions | Evaluation metrics and statistical primitives | REQ-0965–REQ-1087, REQ-1262–REQ-1271 | `I34` | Deterministic metric, missingness/denominator, clustered bootstrap, Wilcoxon/effect/multiplicity tests. |
| §§19.4, 37 | Baseline/calibration workflow artifacts and producer reuse | REQ-1361–REQ-1369, REQ-2934–REQ-2935, REQ-2946–REQ-2951 | `I35` | Baseline/calibration producer manifests and compatible reuse evidence. |
| §23 | Real-data feasibility and control audit | REQ-1599–REQ-1631 | `I36` | Chronology/support/control/client/operator/representation audit manifests and eligibility outcome. |
| §25 | Nested pre-cutoff calibration | REQ-1651–REQ-1719 | `I37` | Inner-cutoff candidate validity, objective selection and immutable calibration-manifest evidence. |
| §36 | Calibration/baseline/evaluation/statistics architecture and tests | REQ-2484–REQ-2485, REQ-2536–REQ-2557, REQ-2586–REQ-2593, REQ-2598–REQ-2605, REQ-2767–REQ-2775, REQ-2789–REQ-2791, REQ-2794–REQ-2796, REQ-2835–REQ-2836, REQ-2845 | `I38` | Roadmap-defined modules, unit/scientific/integration tests and baseline fairness checks. |
| Scope / claim constraints | Comparator novelty/identity boundaries and real-data eligibility claim boundary (`NON_IMPLEMENTATION`; traceability only) | REQ-0844, REQ-0846, REQ-0848, REQ-0850, REQ-0852, REQ-0854, REQ-0856, REQ-0858, REQ-0860, REQ-0862, REQ-0864, REQ-0866, REQ-0868, REQ-1632 | — | Roadmap-to-inventory and claim/scope review confirms the constraints are preserved without creating fictitious implementation work. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation requirement must map to at least one real implementation issue before implementation begins; issue references remain `—` in this milestone-only phase.
- Every conditional requirement remains traceable and is implemented when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when implementation begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M05 — Synthetic Mechanism and Geometry Validation | Verified synthetic/math behavior and compatible FedACT implementation | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Prepared real corpora, cutoffs, splits, checkpoints and scores | M02 | Chronology, support, identity and leakage validation. |
| Validated operator library and action displacements | M03 | Domain-valid/nondegenerate action evidence and matching encoder identity. |
| FedACT set/certificate engine | M04 | Mathematical verification and core scientific tests pass. |
| Synthetic validation evidence | M05 | Mandatory smoke and theory/geometry workflows complete. |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I33` — Implement Comparators and Validate Fairness and Parity | Comparator implementation, fairness and parity validation | `§§14, 24 + linked definitions` | 85 atomic requirements | `I32` |
| 2 | `I34` — Implement Evaluation Metrics and Statistical Primitives | Evaluation metrics and statistical primitives | `§§16–17 + linked definitions` | 133 atomic requirements | `I33` |
| 3 | `I36` — Execute Real-Data Feasibility and Control Audit | Real-data feasibility and control audit | `§23` | 33 atomic requirements | `I34` |
| 4 | `I35` — Implement Baseline and Calibration Workflow Artifact Reuse | Baseline/calibration workflow artifacts and producer reuse | `§§19.4, 37` | 17 atomic requirements | `I34`, `I36` |
| 5 | `I37` — Implement Nested Pre-Cutoff Calibration | Nested pre-cutoff calibration | `§25` | 69 atomic requirements | `I35`, `I36` |
| 6 | `I38` — Implement Calibration, Baseline, Evaluation, and Statistics Architecture | Calibration/baseline/evaluation/statistics architecture and tests | `§36` | 58 atomic requirements | `I37` |
| 7 | `I39` — Audit Real-Data Feasibility, Baselines, Metrics, and Nested Calibration | Independent milestone completion audit and `PASS`/`FAIL` gate | `§§14, 16–17, 19.4, 23–25, 36–37 (feasibility, baseline, evaluation, statistics, and calibration portions)`; Milestone `M06` completion contract: `Exit Criteria`, `Acceptance Evidence`, and `Milestone Audit`. | Audit / milestone-completion gate — no new primary requirements | `I38` |

### Issue Contract

Every milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Real-data feasibility/control/client/operator/representation audit manifests and dataset eligibility outcomes | `I33`, `I34`, `I35`, `I36`, `I37`, `I38` | Chronology, support, control matching, client semantics, operator validity and representation-boundary audits | M07–M09 |
| Required identification/security/federation comparator implementations, checkpoints, scores and parity manifests | `I33`, `I34`, `I35`, `I36`, `I37`, `I38` | Published-implementation identity, fairness constraints, analytical/synthetic parity and chronological evaluation checks | M07–M09 |
| Full-precision metric and statistical-analysis library including missingness/denominator rules | `I33`, `I34`, `I35`, `I36`, `I37`, `I38` | Metric unit tests, clustered bootstrap/Wilcoxon/effect/multiplicity fixtures and deterministic quantile checks | M07–M09 |
| Nested pre-cutoff calibration artifacts for each eligible dataset/external cutoff | `I33`, `I34`, `I35`, `I36`, `I37`, `I38` | Inner-cutoff leakage checks, candidate validity gates, lexicographic objective selection, hardening-weight selection and calibration manifests | M07–M09 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly referenced through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M05 is complete with audit `PASS`.
- Prepared real-data artifacts from M02, operator artifacts from M03, and FedACT core artifacts from M04 are complete and compatible.
- Required public comparator implementations/specifications are acquired where the roadmap makes them eligible; otherwise exact `NOT_APPLICABLE` semantics are preserved.
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- after issue decomposition, every mandatory implementation requirement is mapped to at least one real milestone issue and every mapped requirement has an explicit verification/evidence target;
- no blocking requirement is `UNMAPPED` or `AMBIGUOUS`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- Every real corpus has a terminal feasibility classification with complete chronology/support/control/client/operator/representation audit evidence.
- All required comparators satisfy identity, fairness and parity requirements or are explicitly unavailable/not applicable under the roadmap rule.
- Every metric/statistical primitive handles denominators, pairing, missingness and precision exactly as specified.
- Nested calibration uses only inner pre-cutoff information, selects only permitted dimensions/objectives, and emits immutable calibrated parameters/manifests for downstream cutoffs.
- every mandatory implementation requirement owned by this milestone is satisfied and every applicable conditional requirement is satisfied;
- every mapped implementation issue is closed;
- all required unit, integration, scientific, CLI/runtime, and validation procedures applicable to the milestone pass;
- all required deliverables, artifacts, interfaces, schemas, manifests, and provenance records are complete and valid;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS` with no unresolved blocking finding.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus future requirement-to-issue mapping | Every mandatory/applicable implementation requirement has exactly one primary milestone owner and completed evidence; traced `NON_IMPLEMENTATION` constraints are preserved. |
| Real-data feasibility | Automated §23 manifests and dataset eligibility outcome | Each dataset/cutoff/client/cohort satisfies or explicitly fails the chronology/support/control/operator/representation gates. |
| Baseline parity | Comparator provenance plus analytical/synthetic/chronological parity results | Each confirmatory comparator reproduces expected behavior and meets fairness constraints before use. |
| Metrics | Deterministic metric fixtures and denominator/missingness tests | Coverage, certificate, geometry, detector, exposure and communication metrics match roadmap definitions exactly. |
| Statistics | Cutoff-clustered bootstrap, Wilcoxon, effect-size, quantile and BH fixtures | Statistical primitives preserve cutoff-level dependence and configured inference semantics. |
| Nested calibration | Per-outer-cutoff inner history, candidate grid/results and selected calibration manifest | No external/later-real information enters calibration; selected values follow the locked validity and objective hierarchy. |
| Deliverables / provenance | Required outputs, manifests, dependency identities and compatibility evidence | Outputs are complete, readable, schema-valid, provenance-complete, active, and non-stale. |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings. |

## Milestone Audit

**Audit issue:** `—`

**Audit status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability;
- closure of every mandatory implementation issue;
- completion and passing status of all required tests;
- completion and passing status of all required validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- Baseline implementations may not be approximated when their required public definition/implementation is unavailable.
- Real-data feasibility may yield insufficient/unsupported evidence without altering upstream data or scientific rules.
- Calibration values cannot be changed after the corresponding prospective outcomes are observed.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues; detailed verification checklists belong in the future milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.


---

# M07 — Prospective Action Certification, Hardening, and Ablation Evidence
> **Outcome:** Demonstrate the real-data action-certificate mechanism and prospective defensive consequence, then execute the complete novelty-critical ablation program under matched chronological conditions.
## At a Glance
| Field | Value |
|---|---|
| Roadmap scope | `§§3, 5–6, 15, 19.4, 26–28, 36–37, 42 (prospective, later-real operator-coverage, and ablation portions)` |
| Requirement ownership | `197 implementation-bearing requirements; exact IDs in Coverage` |
| Upstream milestones | `M06` |
| Implementation issues | `I40`, `I41`, `I42`, `I43`, `I44`, `I45`, `I46` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | `I47` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every roadmap requirement owned by this milestone must be explicitly mapped to its future implementation issue(s) and objective verification evidence.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §5 | Prospective certificate and security-consequence evidence | REQ-0157–REQ-0159, REQ-0161–REQ-0163 | `I40` | Later-real certificate-group and hardening consequence evidence on locked cutoff units. |
| §6 | Later-real operator-coverage validation | REQ-0220 | `I41` | Later-real coverage diagnostics verify whether the locked valid operator library supplies meaningful challenge directions on eligible prospective units without altering pre-cutoff operator definitions. |
| §15 | Ablation specifications and claim-critical alternatives | REQ-0917–REQ-0918, REQ-0920–REQ-0921, REQ-0923–REQ-0924, REQ-0926–REQ-0927, REQ-0929–REQ-0930, REQ-0932–REQ-0933, REQ-0935–REQ-0936, REQ-0938–REQ-0939, REQ-0941–REQ-0942, REQ-0944–REQ-0945, REQ-0947–REQ-0948, REQ-0950–REQ-0951, REQ-0953–REQ-0954, REQ-0956–REQ-0957, REQ-0959–REQ-0960, REQ-0962–REQ-0964 | `I42` | Definition validation proves each ablation changes only its named scientific boundary. |
| §26 | Real-data action-certificate validation | REQ-1720–REQ-1754, REQ-1756 | `I43` | Matched action groups, later-real relevance metrics and certificate precision evidence. |
| §27 | Prospective FedACT hardening evaluation | REQ-1757–REQ-1797 | `I44` | Hardened checkpoints, clean-cost eligibility, primary exposure/FNR and comparator outcomes. |
| §28 | Novelty-critical ablation execution | REQ-1799–REQ-1829, REQ-1833–REQ-1834 | `I45` | All mandatory ablation outcome artifacts with matched dependencies and claim-invalidation results. |
| §§19.4, 36–37, 42 | Prospective/ablation workflow architecture, artifacts and CLI | REQ-1370–REQ-1378, REQ-2570–REQ-2575, REQ-2594–REQ-2597, REQ-2781–REQ-2783, REQ-2792–REQ-2793, REQ-2849, REQ-2893–REQ-2907, REQ-3103–REQ-3105, REQ-3171–REQ-3173, REQ-3195 | `I46` | Workflow modules/tests and action-certificate/prospective/ablation command manifests. |
| Scope / claim constraints | Point-vs-set, prospective, hardening, temporal-ordering and ablation claim boundaries plus detector-vs-certificate interpretation (`NON_IMPLEMENTATION`; traceability only) | REQ-0067–REQ-0069, REQ-0076–REQ-0082, REQ-0091–REQ-0093, REQ-0160, REQ-0164, REQ-0916, REQ-0919, REQ-0922, REQ-0925, REQ-0928, REQ-0931, REQ-0934, REQ-0937, REQ-0940, REQ-0943, REQ-0946, REQ-0949, REQ-0952, REQ-0955, REQ-0958, REQ-0961, REQ-1755, REQ-1798, REQ-1830–REQ-1832 | — | Roadmap-to-inventory and claim/scope review confirms the constraints are preserved without creating fictitious implementation work. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation requirement must map to at least one real implementation issue before implementation begins; issue references remain `—` in this milestone-only phase.
- Every conditional requirement remains traceable and is implemented when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when implementation begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M06 — Real-Data Feasibility, Baselines, Metrics, and Nested Calibration | Eligible real-data units, parity-validated baselines, full-precision metrics/statistics, and immutable per-cutoff calibration | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Calibrated feasible sets, action thresholds and temporal parameters | M06 / M04 | Calibration provenance matches the outer cutoff and all M04 scientific invariants pass. |
| Prepared/checkpoint/scoring/operator artifacts | M02 / M03 | Checkpoint, sample, action and cutoff identities are compatible and complete. |
| Comparator parity artifacts | M06 | Required comparator implementations are confirmatory-eligible. |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I43` — Execute Real-Data Action-Certificate Validation | Real-data action-certificate validation | `§26` | 36 atomic requirements | `I39` |
| 2 | `I44` — Execute Prospective FedACT Hardening Evaluation | Prospective FedACT hardening evaluation | `§27` | 41 atomic requirements | `I43` |
| 3 | `I40` — Validate Prospective Certificate and Security-Consequence Evidence | Prospective certificate and security-consequence evidence | `§5` | 6 atomic requirements | `I44` |
| 4 | `I41` — Validate Later-Real Operator Coverage | Later-real operator-coverage validation | `§6` | 1 atomic requirements | `I40` |
| 5 | `I42` — Implement Claim-Critical Ablation Specifications | Ablation specifications and claim-critical alternatives | `§15` | 33 atomic requirements | `I41` |
| 6 | `I45` — Execute Novelty-Critical Ablations | Novelty-critical ablation execution | `§28` | 33 atomic requirements | `I42` |
| 7 | `I46` — Implement Prospective and Ablation Workflow Architecture | Prospective/ablation workflow architecture, artifacts and CLI | `§§19.4, 36–37, 42` | 47 atomic requirements | `I45` |
| 8 | `I47` — Audit Prospective Action Certification, Hardening, and Ablation Evidence | Independent milestone completion audit and `PASS`/`FAIL` gate | `§§3, 5–6, 15, 19.4, 26–28, 36–37, 42 (prospective, later-real operator-coverage, and ablation portions)`; Milestone `M07` completion contract: `Exit Criteria`, `Acceptance Evidence`, and `Milestone Audit`. | Audit / milestone-completion gate — no new primary requirements | `I46` |

### Issue Contract

Every milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Per-cutoff certified, point-positive ambiguous, negative and matched-random valid action-group outcomes | `I40`, `I41`, `I42`, `I43`, `I44`, `I45`, `I46` | Matched-population/action-count validity checks and later-real alignment construction | M08–M09 |
| Certificate precision/relevance evidence and primary ordered comparison inputs | `I40`, `I41`, `I42`, `I43`, `I44`, `I45`, `I46` | Full-precision later-real metrics with required missingness and matched-count handling | M08–M09 |
| Hardened detector checkpoints and prospective baseline/FedACT outcomes | `I40`, `I41`, `I42`, `I43`, `I44`, `I45`, `I46` | Frozen-encoder hardening validation, clean-cost checkpoint gate, chronological later-real evaluation and exposure metrics | M08–M09 |
| Complete novelty-critical ablation outcomes | `I40`, `I41`, `I42`, `I43`, `I44`, `I45`, `I46` | Single-boundary manipulation checks, matched upstream artifacts and claim-invalidation evidence | M08–M09 |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly referenced through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M06 is complete with audit `PASS`.
- Each included real-data unit has valid preparation, operator, base-model, FedACT, baseline-parity and nested-calibration artifacts.
- Later-real evaluation data remain unread until the corresponding scientific inputs and decision artifacts are complete.
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- after issue decomposition, every mandatory implementation requirement is mapped to at least one real milestone issue and every mapped requirement has an explicit verification/evidence target;
- no blocking requirement is `UNMAPPED` or `AMBIGUOUS`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- Action-certificate validation compares the exact prescribed action groups with matched counts/validity, produces later-real relevance evidence, and completes the §6 operator-coverage validation using later-real coverage diagnostics.
- Prospective hardening uses only certified valid actions, completes before later-real evaluation, and reports primary exposure/FNR outcomes plus clean-data cost.
- All mandatory ablations vary only the named scientific boundary and reuse otherwise compatible artifacts.
- Any null/adverse result triggers the roadmap-defined interpretation rather than post hoc method or threshold changes.
- every mandatory implementation requirement owned by this milestone is satisfied and every applicable conditional requirement is satisfied;
- every mapped implementation issue is closed;
- all required unit, integration, scientific, CLI/runtime, and validation procedures applicable to the milestone pass;
- all required deliverables, artifacts, interfaces, schemas, manifests, and provenance records are complete and valid;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS` with no unresolved blocking finding.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus future requirement-to-issue mapping | Every mandatory/applicable implementation requirement has exactly one primary milestone owner and completed evidence; traced `NON_IMPLEMENTATION` constraints are preserved. |
| Certificate mechanism | Per-cutoff action-group records, later-real proxy/alignment, precision/recall, matched-random evidence, and later-real operator-coverage diagnostics | The prespecified certified versus ambiguous versus matched-random comparison is computable on eligible paired cutoffs, and the locked operator library's later-real coverage is explicitly measured without post-cutoff redesign. |
| Hardening correctness | Challenge-selection provenance, frozen-encoder checks, hardening objective/checkpoint eligibility and clean-cost evidence | Only certified valid challenges affect hardening; checkpoint selection follows the locked objective and clean-cost gate. |
| Prospective security | Early-horizon FNR/exposure curves and required comparator outcomes | All later-real windows are complete, chronological and evaluated with prespecified endpoints. |
| Ablations | Ablation manifests proving only the named boundary changed | Every novelty-critical ablation is complete and matched to the same relevant upstream artifacts/budgets. |
| Failure/claim interpretation | Terminal scientific outcomes and claim-invalidation records | Null, adverse, insufficient or invalidating results are preserved exactly and do not cause post-outcome redesign. |
| Deliverables / provenance | Required outputs, manifests, dependency identities and compatibility evidence | Outputs are complete, readable, schema-valid, provenance-complete, active, and non-stale. |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings. |

## Milestone Audit

**Audit issue:** `—`

**Audit status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability;
- closure of every mandatory implementation issue;
- completion and passing status of all required tests;
- completion and passing status of all required validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- Detector performance alone cannot establish the FedACT contribution if the action-certificate mechanism fails.
- Point-positive actions remain comparator quantities and do not replace set-valued certification.
- Ablations are fixed tests of contribution boundaries, not opportunities to redesign the method.
- Temporal-ordering evidence and later-real operator-coverage diagnostics are evaluated only after their pre-cutoff scientific inputs are locked; neither may be used to redesign the temporal method or operator library.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues; detailed verification checklists belong in the future milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.


---

# M08 — Federation, Robustness, Cross-Corpus, and Client-Selection Evaluation
> **Outcome:** Complete the federation/complementarity, graceful-failure, robustness, cross-corpus generalization, and optional equal-budget client-selection studies with the roadmap’s explicit claim limits.
## At a Glance
| Field | Value |
|---|---|
| Roadmap scope | `§§3, 5, 19.4, 29–32, 36–37, 42 (federation, robustness, generalization, and client-selection portions)` |
| Requirement ownership | `208 implementation-bearing requirements; exact IDs in Coverage` |
| Upstream milestones | `M07` |
| Implementation issues | `I48`, `I49`, `I50`, `I51`, `I52`, `I53` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | `I54` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every roadmap requirement owned by this milestone must be explicitly mapped to its future implementation issue(s) and objective verification evidence.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §§3, 5 | Graceful-failure hypothesis and evidence | REQ-0084–REQ-0089, REQ-0165–REQ-0167 | `I48` | Locked failure-factor experiments produce interval/ambiguity/abstention diagnostics or falsification. |
| §29 | Federation and complementarity evaluation | REQ-1835–REQ-1877 | `I49` | Matched local/federated/redundant/complementary/centralized/randomized geometry contrasts. |
| §30 | Robustness and failure-boundary evaluation | REQ-1878–REQ-1898, REQ-1900–REQ-1930 | `I50` | One-factor boundary/corruption manifests, curves and taxonomy-consistent outcomes. |
| §31 | Cross-corpus generalization | REQ-1931–REQ-1956 | `I51` | EMBER2024 unchanged-semantics execution and eligibility/claim evidence. |
| §32 | Optional communication-limited client selection | REQ-1958–REQ-1974, REQ-1976–REQ-1984 | `I52` | Equal-budget selector comparison and communication-normalized action-width evidence when applicable. |
| §§19.4, 36–37, 42 | Federation/robustness/generalization workflow architecture and CLI | REQ-1379–REQ-1390, REQ-2576–REQ-2583, REQ-2784–REQ-2787, REQ-2908–REQ-2927, REQ-3106–REQ-3109, REQ-3196–REQ-3198, REQ-3291 | `I53` | Workflow modules/tests and federation/failure/cross-corpus/client-selection command manifests. |
| Scope / claim constraints | Complementarity, graceful-failure, cross-corpus/client-selection hypotheses and non-identification claim limits (`NON_IMPLEMENTATION`; traceability only) | REQ-0070–REQ-0072, REQ-0083, REQ-0090, REQ-0094–REQ-0099, REQ-0168, REQ-1899, REQ-1957 | — | Roadmap-to-inventory and claim/scope review confirms the constraints are preserved without creating fictitious implementation work. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation requirement must map to at least one real implementation issue before implementation begins; issue references remain `—` in this milestone-only phase.
- Every conditional requirement remains traceable and is implemented when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when implementation begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M07 — Prospective Action Certification, Hardening, and Ablation Evidence | Validated prospective mechanism/outcomes and compatible artifacts needed by downstream federation, robustness, and generalization workflows | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Prospective evaluation and certificate artifacts | M07 | Complete, compatible cutoff/checkpoint/action identities and valid terminal outcomes. |
| Synthetic geometry/failure fixtures | M05 | Known-truth generator and sweep artifacts pass smoke/theory validation. |
| EMBER2024 prepared/trained/scored/calibrated artifacts | M02 / M06 | Cross-corpus chronology, feasibility, representation, operator and calibration gates pass where applicable. |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I48` — Validate Graceful Failure and Abstention Evidence | Graceful-failure hypothesis and evidence | `§§3, 5` | 9 atomic requirements | `I47` |
| 2 | `I49` — Execute Federation and Complementarity Evaluation | Federation and complementarity evaluation | `§29` | 43 atomic requirements | `I48` |
| 3 | `I50` — Execute Robustness and Failure-Boundary Evaluation | Robustness and failure-boundary evaluation | `§30` | 52 atomic requirements | `I49` |
| 4 | `I51` — Execute Cross-Corpus Generalization | Cross-corpus generalization | `§31` | 26 atomic requirements | `I50` |
| 5 | `I52` — Implement Optional Communication-Limited Client Selection | Optional communication-limited client selection | `§32` | 26 atomic requirements | `I51` |
| 6 | `I53` — Implement Federation, Robustness, and Generalization Workflow Architecture | Federation/robustness/generalization workflow architecture and CLI | `§§19.4, 36–37, 42` | 52 atomic requirements | `I52` |
| 7 | `I54` — Audit Federation, Robustness, Cross-Corpus, and Client-Selection Evaluation | Independent milestone completion audit and `PASS`/`FAIL` gate | `§§3, 5, 19.4, 29–32, 36–37, 42 (federation, robustness, generalization, and client-selection portions)`; Milestone `M08` completion contract: `Exit Criteria`, `Acceptance Evidence`, and `Milestone Audit`. | Audit / milestone-completion gate — no new primary requirements | `I53` |

### Issue Contract

Every milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Local-versus-federated, redundant-versus-complementary, centralized-equivalence and randomized-geometry contrasts | `I48`, `I49`, `I50`, `I51`, `I52`, `I53` | Matched samples/noise/cutoffs, constraint-package integrity, and precision-vs-identification gain diagnostics | M09 |
| Robustness/failure-boundary curves and diagnostics | `I48`, `I49`, `I50`, `I51`, `I52`, `I53` | One-factor stress manifests across sparse controls, eigengap, span/private/synchronized nuisance, action geometry, horizon, temporal predictability and corrupted summaries | M09 |
| Cross-corpus mechanism/outcome evidence on eligible EMBER2024 Win32/Win64 units | `I48`, `I49`, `I50`, `I51`, `I52`, `I53` | Unchanged estimand/certification semantics, corpus-specific eligibility and chronological evaluation validation | M09 |
| Optional equal-communication-budget client-selection outcomes when enabled/eligible | `I48`, `I49`, `I50`, `I51`, `I52`, `I53` | Budget matching, selector definitions, per-client/byte width reduction and secondary certificate consequences | M09 / optional reporting |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly referenced through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M07 is complete with audit `PASS`.
- Synthetic known-truth and real prospective artifacts required by each stress/federation condition are complete and dependency-compatible.
- Cross-corpus/client-selection conditions execute only when their roadmap-defined eligibility conditions hold.
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- after issue decomposition, every mandatory implementation requirement is mapped to at least one real milestone issue and every mapped requirement has an explicit verification/evidence target;
- no blocking requirement is `UNMAPPED` or `AMBIGUOUS`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- Federation experiments distinguish precision gain from identification gain and enforce the strong-federation claim criterion.
- Failure-boundary studies show the actual interval/certification/abstention response under each locked manipulation and preserve method-failure versus assumption-violation versus fundamental-nonidentification distinctions.
- Cross-corpus execution preserves the FedACT estimand and certification semantics unchanged and records the allowed generalization claim state.
- Optional client selection is either completed under equal communication budgets when applicable or explicitly omitted/not applicable without blocking mandatory synthesis.
- every mandatory implementation requirement owned by this milestone is satisfied and every applicable conditional requirement is satisfied;
- every mapped implementation issue is closed;
- all required unit, integration, scientific, CLI/runtime, and validation procedures applicable to the milestone pass;
- all required deliverables, artifacts, interfaces, schemas, manifests, and provenance records are complete and valid;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS` with no unresolved blocking finding.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus future requirement-to-issue mapping | Every mandatory/applicable implementation requirement has exactly one primary milestone owner and completed evidence; traced `NON_IMPLEMENTATION` constraints are preserved. |
| Federation | Matched local/federated/redundant/complementary/centralized/randomized-geometry contrasts | All conditions share the required support/noise/cutoff basis; geometry and certificate consequences are reported separately. |
| Graceful failure | Interval-width, certification-rate, abstention and synchronized-nuisance diagnostics across locked boundaries | Increasing irreducible ambiguity does not create unjustified confidence; outcomes are classified by the roadmap taxonomy. |
| Corruption stress | Deterministic corrupted-client/count/attack manifests and diagnostics | Only the declared summary corruption changes; no formal Byzantine-security claim is inferred. |
| Cross-corpus | EMBER2024 chronology/eligibility plus unchanged-mechanism results | Mechanism chain is evaluated without changing the primary estimand or certification semantics. |
| Client selection | Equal-budget selection records and communication-normalized width-reduction metrics | When run, action-focused selection is compared with random, sample-count and global-information selectors under the same budget. |
| Deliverables / provenance | Required outputs, manifests, dependency identities and compatibility evidence | Outputs are complete, readable, schema-valid, provenance-complete, active, and non-stale. |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings. |

## Milestone Audit

**Audit issue:** `—`

**Audit status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability;
- closure of every mandatory implementation issue;
- completion and passing status of all required tests;
- completion and passing status of all required validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- FedACT does not claim formal Byzantine security, deployment readiness, or universal organizational generalization.
- Synchronized nuisance without an independent control signature remains non-identifiable and cannot support a success claim.
- Client selection is secondary and optional; intentional omission does not block mandatory statistical synthesis.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues; detailed verification checklists belong in the future milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.


---

# M09 — Statistical Synthesis, Claim Adjudication, and Manuscript Evidence
> **Outcome:** Convert all verified mandatory workflow outcomes into prespecified statistical conclusions, bounded claim states, and reproducible manuscript-facing tables, figures, appendices, and evidence indexes without recomputation.
## At a Glance
| Field | Value |
|---|---|
| Roadmap scope | `§§33, 35–37, 42–43 (statistical-synthesis, claim, analysis, and reporting portions)` |
| Requirement ownership | `200 implementation-bearing requirements; exact IDs in Coverage` |
| Upstream milestones | `M08` |
| Implementation issues | `I55`, `I56`, `I57`, `I58`, `I59` |
| Coverage authority | `Roadmap Coverage Inventory` |
| Audit issue | `I60` |
| Audit status | `PENDING` |

## Coverage

The Roadmap Coverage Inventory is the traceability authority for this milestone. Every roadmap requirement owned by this milestone must be explicitly mapped to its future implementation issue(s) and objective verification evidence.

| Roadmap Section | Scope / Work Package | Requirement IDs | Implementation Issue(s) | Verification / Evidence |
|---|---|---|---|---|
| §33 + linked definitions | Statistical synthesis and sensitivity adjudication | REQ-1274–REQ-1275, REQ-1985–REQ-2013 | `I55` | Prespecified paired contrasts, multiplicity, sensitivity and layer-specific outcome synthesis. |
| §35.1 | Claim-evidence adjudication | REQ-2112, REQ-2114, REQ-2116, REQ-2118, REQ-2120, REQ-2122, REQ-2124, REQ-2126, REQ-2128, REQ-2130, REQ-2132, REQ-2134, REQ-2136, REQ-2138, REQ-2140, REQ-2142, REQ-2144, REQ-2146, REQ-2148, REQ-2150, REQ-2152, REQ-2154, REQ-2156–REQ-2157, REQ-2159–REQ-2160, REQ-2162–REQ-2165 | `I56` | Claim/evidence matrix applies exact support/falsification/insufficient criteria with no stronger wording. |
| §§35.2–35.4 | Manuscript tables, figures, appendix evidence and completion gates | REQ-2166–REQ-2227, REQ-2229–REQ-2231 | `I57` | Locked render outputs and research-completion checks from verified full-precision evidence. |
| §36 | Analysis/reporting architecture and tests | REQ-2584–REQ-2585, REQ-2606–REQ-2611, REQ-2648–REQ-2659, REQ-2788, REQ-2797–REQ-2799, REQ-2837, REQ-2856–REQ-2858 | `I58` | Analysis/reporting modules plus scientific claim-boundary and verified-export integration tests. |
| §§19.4, 37, 39, 42–43 | Statistical-synthesis/reporting workflow and verified export | REQ-1391–REQ-1393, REQ-2928–REQ-2932, REQ-3018, REQ-3097–REQ-3098, REQ-3110, REQ-3134–REQ-3136, REQ-3181–REQ-3187, REQ-3199, REQ-3218–REQ-3229, REQ-3242–REQ-3245, REQ-3286–REQ-3290, REQ-3295–REQ-3296 | `I59` | Statistical-synthesis/report commands, results filtering, stale-export removal, evidence index and reproducibility package. |
| Scope / claim constraints | Manuscript claim-state and reporting claim boundaries (`NON_IMPLEMENTATION`; traceability only) | REQ-2113, REQ-2115, REQ-2117, REQ-2119, REQ-2121, REQ-2123, REQ-2125, REQ-2127, REQ-2129, REQ-2131, REQ-2133, REQ-2135, REQ-2137, REQ-2139, REQ-2141, REQ-2143, REQ-2145, REQ-2147, REQ-2149, REQ-2151, REQ-2153, REQ-2155, REQ-2158, REQ-2161, REQ-2228 | — | Roadmap-to-inventory and claim/scope review confirms the constraints are preserved without creating fictitious implementation work. |

### Coverage Rules

- Every mandatory requirement owned by this milestone must be present in the Roadmap Coverage Inventory.
- Every mandatory implementation requirement must map to at least one real implementation issue before implementation begins; issue references remain `—` in this milestone-only phase.
- Every conditional requirement remains traceable and is implemented when its roadmap-defined condition applies.
- Every mapped requirement must have objective verification or evidence.
- Every implementation issue must reference the exact requirement IDs it satisfies.
- A requirement is not considered covered merely because it falls inside a requirement range or roadmap section assigned to the milestone.
- No blocking requirement may remain `UNMAPPED` or `AMBIGUOUS` when implementation begins.
- No issue may redefine, weaken, silently reinterpret, duplicate, or extend the authoritative roadmap requirement it implements.

## Dependencies

### Milestone Dependencies

| Milestone | Required Input / Contract | Entry Gate |
|---|---|---|
| M08 — Federation, Robustness, Cross-Corpus, and Client-Selection Evaluation | All mandatory confirmatory workflow evidence; optional client-selection evidence when intentionally executed | `Complete + audit PASS` |

### Artifact / Interface Dependencies

| Dependency | Produced By | Required Validation |
|---|---|---|
| Verified full-precision outcomes from mandatory workflows | M05–M08 | Artifact status COMPLETE/valid, compatible provenance, complete required populations, and no stale dependencies. |
| Statistical primitives and metric records | M06 | Cutoff-level pairing/missingness/denominator/statistical validation passes. |
| Global scientific/claim-boundary contract | M01 and milestone-specific NON_IMPLEMENTATION constraints | Terminology, novelty exclusions, scope limitations and falsification rules remain unchanged. |

Dependency completion alone is not sufficient. Every consumed dependency must be present, valid, provenance-compatible where applicable, and compatible with the active roadmap contract.

## Implementation Issues

Implementation issues for this milestone are listed below; each issue's detailed task checklist, acceptance criteria, and required tests are defined in `Issues.md`.

| Order | Issue | Work Package | Roadmap Scope | Requirement Coverage | Depends On |
|---:|---|---|---|---|---|
| 1 | `I55` — Execute Statistical Synthesis and Sensitivity Adjudication | Statistical synthesis and sensitivity adjudication | `§33 + linked definitions` | 31 atomic requirements | `I54` |
| 2 | `I56` — Adjudicate Claims Against Verified Evidence | Claim-evidence adjudication | `§35.1` | 30 atomic requirements | `I55` |
| 3 | `I57` — Produce Manuscript Tables, Figures, Appendix Evidence, and Completion Gates | Manuscript tables, figures, appendix evidence and completion gates | `§§35.2–35.4` | 65 atomic requirements | `I56` |
| 4 | `I58` — Implement Analysis and Reporting Architecture | Analysis/reporting architecture and tests | `§36` | 28 atomic requirements | `I57` |
| 5 | `I59` — Implement Statistical Synthesis, Reporting Workflow, and Verified Export | Statistical-synthesis/reporting workflow and verified export | `§§19.4, 37, 39, 42–43` | 46 atomic requirements | `I58` |
| 6 | `I60` — Audit Statistical Synthesis, Claim Adjudication, and Manuscript Evidence | Independent milestone completion audit and `PASS`/`FAIL` gate | `§§33, 35–37, 42–43 (statistical-synthesis, claim, analysis, and reporting portions)`; Milestone `M09` completion contract: `Exit Criteria`, `Acceptance Evidence`, and `Milestone Audit`. | Audit / milestone-completion gate — no new primary requirements | `I59` |

### Issue Contract

Every milestone issue must:

- reference its exact roadmap section(s);
- list every covered requirement ID;
- contain a detailed implementation checklist;
- define objective acceptance criteria;
- identify required tests;
- identify required artifacts, outputs, or interfaces;
- identify required provenance or manifest updates where applicable;
- identify explicit dependencies on upstream milestones, issues, artifacts, or interfaces;
- preserve roadmap terminology and semantics;
- close only when every mapped requirement and acceptance criterion is satisfied.

## Deliverables

| Deliverable | Source Issue(s) | Required Validation | Downstream Consumer |
|---|---|---|---|
| Prespecified paired contrasts, confidence intervals, hypothesis tests, effect sizes, multiplicity results and sensitivity surfaces | `I55`, `I56`, `I57`, `I58`, `I59` | Cutoff-clustered inference validation, minimum-pair/missingness gates and deterministic full-precision reconstruction | Manuscript evidence |
| Claim-state evidence mapping for every roadmap claim | `I55`, `I56`, `I57`, `I58`, `I59` | Evidence-to-claim rule validation yielding supported/falsified/partial/insufficient states without stronger wording | Manuscript |
| Locked main/supplementary tables, figures and appendix evidence | `I55`, `I56`, `I57`, `I58`, `I59` | Render-only validation from verified full-precision artifacts; presentation rounding only at reporting layer | Manuscript |
| Compact reproducibility package and evidence index under `results/` | `I55`, `I56`, `I57`, `I58`, `I59` | Traceability from every manuscript number to active full-precision artifacts/provenance; stale-parent export removal tests | Manuscript / independent verification |

All roadmap-required deliverables for this milestone must appear in this table or be explicitly referenced through the Roadmap Coverage Inventory.

## Entry Criteria

Implementation may begin only when all of the following are true:

- M08 is complete with audit `PASS`; all mandatory workflow artifacts needed by §33/§35 have terminal valid scientific outcomes.
- Optional client-selection evidence is included only if the optional workflow was intentionally executed and eligible.
- No stale, invalid, incomplete or provenance-incompatible source artifact is eligible for synthesis/reporting.
- all roadmap requirements owned by this milestone are present in the Roadmap Coverage Inventory;
- after issue decomposition, every mandatory implementation requirement is mapped to at least one real milestone issue and every mapped requirement has an explicit verification/evidence target;
- no blocking requirement is `UNMAPPED` or `AMBIGUOUS`;
- no unresolved roadmap ambiguity would force the implementer to invent a scientific, mathematical, methodological, numerical, architectural, configuration, artifact, or execution decision.

## Exit Criteria

The milestone is complete only when all of the following are true:

- Statistical synthesis preserves cutoff-level dependence, prespecified contrasts, multiplicity and sensitivity semantics, and all required missingness/evidence gates.
- Every manuscript claim is assigned only the support state justified by its required evidence; all global and milestone-specific claim boundaries are preserved.
- Every required table, figure, appendix item, metric/statistical export and reproducibility artifact is generated from verified full-precision sources without scientific recomputation.
- Every manuscript number is traceable through the evidence index to complete active scientific/analysis artifacts and provenance, and stale exports are excluded/regenerated only after valid recomputation.
- every mandatory implementation requirement owned by this milestone is satisfied and every applicable conditional requirement is satisfied;
- every mapped implementation issue is closed;
- all required unit, integration, scientific, CLI/runtime, and validation procedures applicable to the milestone pass;
- all required deliverables, artifacts, interfaces, schemas, manifests, and provenance records are complete and valid;
- no required evidence is stale or incompatible with its material dependencies;
- the milestone audit is `PASS` with no unresolved blocking finding.

## Acceptance Evidence

| Evidence Area | Required Evidence | Pass Condition |
|---|---|---|
| Requirement coverage | Roadmap Coverage Inventory plus future requirement-to-issue mapping | Every mandatory/applicable implementation requirement has exactly one primary milestone owner and completed evidence; traced `NON_IMPLEMENTATION` constraints are preserved. |
| Statistical synthesis | Paired-cutoff source records, clustered BCa intervals, Wilcoxon/effect-size outputs, BH results and sensitivity surfaces | All prespecified analyses execute on valid populations with required paired-cutoff and missingness gates. |
| Claim adjudication | Claim/evidence matrix with terminal support state and decisive evidence references | No claim exceeds the roadmap criterion; falsification/partial/insufficient outcomes are retained. |
| Reporting | Rendered main/supplementary tables/figures and appendix evidence derived from verified analysis artifacts | Outputs match fixed reporting semantics; only presentation formatting/rounding changes values displayed. |
| Evidence traceability | Project/experiment evidence indexes and exact source artifact identities | Every reported number/figure/table traces to active full-precision source evidence and provenance. |
| Reproducibility | Compact execution/config/environment/dependency evidence plus verified regeneration tests | Reporting can be regenerated without retraining, rescoring, recalibrating, reevaluating or altering statistical decisions. |
| Deliverables / provenance | Required outputs, manifests, dependency identities and compatibility evidence | Outputs are complete, readable, schema-valid, provenance-complete, active, and non-stale. |
| Audit | Milestone audit issue | Final result is `PASS` with no unresolved blocking findings. |

## Milestone Audit

**Audit issue:** `—`

**Audit status:** `PENDING`

The milestone audit is the final completion gate. It must independently verify:

- complete roadmap coverage for all requirements owned by the milestone;
- exact requirement-to-issue traceability;
- closure of every mandatory implementation issue;
- completion and passing status of all required tests;
- completion and passing status of all required validations;
- existence and validity of all required deliverables;
- completeness and validity of required provenance and manifests;
- absence of stale or incompatible evidence;
- absence of unresolved blocking findings;
- readiness of milestone outputs for all declared downstream consumers.

The audit must end in exactly one result:

- `PASS` — every completion condition is satisfied.
- `FAIL` — one or more blocking conditions remain.

A milestone is not complete until the audit result is `PASS`.

## Scope Boundary

- M09 reports and adjudicates evidence; it may not change scientific configuration, calibration, methods, comparisons, thresholds, datasets, or earlier outcomes.
- `results/` is manuscript-facing output only and is never a scientific execution input.
- Global method-name, novelty-credit, exclusion, non-identification and claim-boundary constraints from M01 and all milestone-specific NON_IMPLEMENTATION rows remain binding.
- This milestone implements only the roadmap requirements explicitly assigned to it.
- The authoritative roadmap remains the source of scientific, mathematical, methodological, architectural, numerical, configuration, artifact, and execution requirements.
- This milestone may organize implementation work but may not redefine, weaken, extend, or silently reinterpret the roadmap.
- Detailed implementation checklists belong in implementation issues; detailed verification checklists belong in the future milestone audit issue.
- Work outside this milestone's mapped roadmap scope must not be added unless the roadmap or coverage inventory is explicitly updated first.
