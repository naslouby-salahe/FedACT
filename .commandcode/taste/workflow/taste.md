# User Taste — Workflow & Tooling

- Prefers multiple incremental commits and pushes throughout work, not one giant commit at the end. Confidence: 0.95
- No AI/Claude co-authorship in git commits; when committing, do not add a co-author trailer unless explicitly requested ("Do not add yourself as coauthor"). Confidence: 0.97
- Testing is mandatory: run format, lint, typecheck, unit tests, integration tests, architecture tests, smoke tests, real-data preprocessing validation, and lightweight real-data training/evaluation smoke. Fix failures rather than weakening test configuration. Confidence: 0.9
- CUDA availability must be detected from the current machine, not assumed. Preserve automatic device selection. Do not hardcode CUDA or CPU, do not make the project CPU-only, do not remove CUDA support. Behavior must remain portable. Confidence: 0.85
- Verify preprocessing and training against real data, not just synthetic tests or successful constructor instantiation. Run real-data smoke execution where full experiments would be too expensive. Confidence: 0.85
- Uses uv as the Python package/dependency manager (uv run, uv add, uv remove). Confidence: 0.85
- Uses ruff for formatting and linting, pyright for type checking, vulture for dead-code detection, deptry for dependency hygiene, import-linter for import contracts, nox as the quality-gate runner. Confidence: 0.85
- Before finishing, performs a hostile audit verifying roadmap alignment, empirical dataset correctness, strong typing, enum usage, absence of primitive contracts, and full test passage. Confidence: 0.8
- When asked to audit, apply the fixes rather than merely reporting them ("Fix what you find rather than merely reporting it. Do not simply produce an audit report. Apply the fixes."). Confidence: 0.85
- Preserve and do not weaken existing architecture test suites and enforcement rules during a refactor; adapt them only where the canonical production tree itself changed, and never relax their fail-closed rules. Confidence: 0.85
- For large refactors, prefers all changes left in the working tree for review — no commits, no pushes, no PRs created or modified — until the user explicitly says to "commit and push all"; only then stage the full repo (excluding session-local tooling/state dirs) and push to the default branch. Confidence: 0.8
