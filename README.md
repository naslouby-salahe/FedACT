# FedACT — Federated Action-Certified Threat Dynamics

FedACT is a federated, chronologically valid method that identifies a control-compatible
shared threat-transition set and certifies domain-valid defensive actions whose support
interval is decision-identifiable relative to that set. Point identification of the full
latent transition is not required; decision ambiguity remains explicit and abstention is a
valid scientific outcome.

## Scientific scope

The authoritative scientific specification is `docs/Roadmap.md`. It defines the estimand,
algorithm contract, chronology rules, datasets, operators, baselines, ablations, metrics,
statistical protocol, provenance requirements, and manuscript evidence. Implementation code
defers to it; no scientific value is invented at runtime.

`configs/fedact.yaml` is the single authoritative production configuration. It must remain
byte-identical to the roadmap Configuration YAML block, which an architecture test enforces.
`configs/tests.yml` and `configs/smoke.yml` are scale-reduced overlays for deterministic
lightweight fixtures and fast smoke validation.

## Setup

```sh
make setup
```

This creates a locked environment from `pyproject.toml` and `uv.lock`.

## Checks

```sh
make checks
```

Equivalent nox sessions are available through `noxfile.py` (`lint`, `typing`, `unit`,
`architecture`). The architecture suite enforces dependency directions, configuration
ownership, governed-value hardcoding, naming policy, canonical vocabulary, typing, formatting,
dead code, dependency hygiene, and the absence of comments, docstrings, redirects, and
temporary residue.

## Canonical CLI workflow

The `fedact` console command exposes only roadmap-authorized public commands:

```sh
fedact doctor
fedact preprocess
fedact plan
fedact smoke
fedact run <workflow>
fedact status
fedact report
```

Raw datasets under `data/raw` are immutable. Generated state lives under git-ignored
`outputs/` (reusable computational artifacts) and `results/` (compact verified
manuscript-facing evidence). Scientific execution never reads from `results/`.
