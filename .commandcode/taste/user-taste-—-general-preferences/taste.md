# User Taste — General Preferences
- Prefers autonomous work: asks the agent to complete everything without asking clarifying questions ("no more questions until all is perfect"). Confidence: 0.85
- Gives highly detailed, prescriptive instructions with explicit constraints and expects them to be followed exactly. Confidence: 0.9
- Values empirical verification over documentation: "real data is authoritative" — dataset facts must be verified from actual files, not trusted from prose. Confidence: 0.9
- Wants surgical refactoring, not rewrites or purges: do not delete working functionality, do not mass-delete files, understand purpose before removing. Confidence: 0.9
- Distinguishes scientific protocol (must remain stable) from empirical dataset facts (must match real data) — will not preserve false numbers just because they were in documentation. Confidence: 0.85
- Prefers following an authoritative specification exactly, with a strict authority hierarchy: the given architecture specification (file tree in the prompt) is the absolute source of truth; an existing roadmap document is authoritative only for scientific meaning (math, algorithms, methodology, dataset semantics, experimental design) and must be rewritten to match the canonical code tree — it must not dictate file placement, module names, runtime architecture, or implementation libraries. Confidence: 0.9
