---
title: "Deep Residual Learning for Image Recognition"
authors: "He, Zhang, Ren, Sun (2015)"
ara_version: "1.0"
---

# Root Manifest

This `ara/` is built entirely by `research-manager`, turn by turn, replaying the
research trajectory the paper itself narrates (§1, §3, §4) as a sequence of real,
source-cited events — see `examples/skills-test-demo/prompts/research-manager-trajectory.md`
for the trajectory and `trace/sessions/2026-07-27_001.yaml` for the turn-by-turn record.

No `logic/experiments.md`, `logic/concepts.md`, `logic/related_work.md`, or `src/` —
those are compiler-owned layers (see `skills/compiler`); this artifact exercises
research-manager only, so only the files research-manager actually writes exist here.

## Layer Index

- `logic/problem.md` — the research question that opens the trajectory
- `logic/claims.md` — 8 claims, crystallized during the trajectory
- `logic/solution/heuristics.md` — 6 heuristics, crystallized during the trajectory
- `trace/exploration_tree.yaml` — 16 journey-fact nodes (question/decision/experiment/dead_end/pivot)
- `trace/taste_log.yaml` — live taste-comment reactions on trace nodes
- `staging/observations.yaml` — the crystallization buffer, all 14 observations promoted
- `trace/sessions/` — the turn-by-turn record
- `evidence/README.md` — pointer to where the underlying numbers live
