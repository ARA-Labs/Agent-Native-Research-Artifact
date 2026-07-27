# Heuristics

## H04: Directional verification over exact numerical matching
- **Rationale**: Legacy papers routinely omit details needed for exact reproduction. Verifying directional properties (A > B on metric X) demonstrates the code kernel captures the core algorithmic insight without requiring exact numerical matches that are impossible from incomplete specifications.
- **Provenance**: user
- **Sensitivity**: medium
- **Code ref**: [paper/sections/protocol.tex — Seal Level 3]
- **Taste** (optional):
  - [2026-07-27] `endorse` on `claim` — Agree: chasing exact numbers from an underspecified legacy paper would've been wasted effort; directional checks are the right bar here.
