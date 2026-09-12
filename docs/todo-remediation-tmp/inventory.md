# TODO remediation inventory

Initial scan: 2026-09-12. Scope is every `TODO`, `FIXME`, `HACK`, `XXX`, `TBD`,
`PENDING`, and `NotImplemented` marker outside this temporary ledger.

The authoritative line-by-line initial scan is captured below by source module; each
entry has its exact file/line and text in the command transcript for this remediation
run. The source inventory contains 221 markers in 27 production modules. Test fixture
strings and policy documentation are tracked separately because they intentionally
refer to markers rather than represent unfinished production work.

| Area | Locations / count | Root cause and disposition |
|---|---:|---|
| Domain vocabulary | `domain/types.py` (30) | Broad aliases were incorrectly labelled as enums. Retained open identifiers as semantic aliases; added closed LAMDA and workflow-artifact enums. `REVIEWED` |
| Artifact/workflow paths | `artifacts.py` (5), `workflow.py` (7), `experiments/{registry,robustness,validation,identification,generalization,ember2024_identification}.py` (52) | Repeated workflow/artifact string literals bypass canonical workflow vocabulary. `registry.py` and `robustness.py` are `VERIFIED`; remaining modules are `DISCOVERED`. |
| APK feature and mutation workflows | `data/{lamda_apk_features,lamda_apk_mutations,lamda_apk_emulator}.py` (36), `experiments/lamda_action_generation.py` (23) | Raw strings cross domain interfaces, and fixed XML/tool/path domains lack types. Trace the end-to-end APK pipeline. `DISCOVERED` |
| Data/config loading | `data/{lamda,ember2024,androzoo,clamav_signatures,synthetic}.py` (20), `config/{loading,models}.py` (7) | Semantic identifiers and raw mappings are insufficiently named; LAMDA location/config ownership must be reviewed. `DISCOVERED` |
| Learning/certification/reporting/CLI | `learning/federation.py` (3), `certification/actions.py` (9), `analysis/{comparisons,reporting}.py` (21), `cli.py` (7) | Closed string domains and named scalar/container types are missing or inconsistently used. `DISCOVERED` |

Initial non-production references: `docs/Roadmap.md:5684,5708`; `.commandcode/taste/coding-style/taste.md:11`; and intentional scanner-fixture literals in `tests/architecture/test_source_hygiene.py` (6). These are `REVIEWED` as documentation/test coverage, not source TODOs.

## Marker classes

- **Enum/path markers:** fixed workflow names, artifact filenames, command/tool names, manifest fields, and reporting identifiers. Requires enum or canonical typed constant only where the domain is closed.
- **Primitive-boundary markers:** named identifiers, records, mappings, XML/APK/emulator values and serialization payloads. Requires semantic aliases or structured records, propagated through callers/callees.
- **Configuration markers:** LAMDA paths and feature prefix. Requires review of configuration ownership before changing behavior.

Every source marker begins `DISCOVERED`; final dispositions will be reconciled in this document after the final scan.
