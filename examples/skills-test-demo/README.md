# ARA Skills Test Demo

A living regression example, shared across the ARA skills. Contributors run this
locally — no CI wiring, no install step, no API key, no automated pass/fail check.

## How this works

One shared `ara/`, exercised by any number of skill-specific prompts. Each prompt
demonstrates that skill's **entire** pipeline working end-to-end on a real research
trajectory — not just one capability in isolation — because the judgment on whether
a skill change is good is a human reading the resulting ARA, which is inherently
subjective and can't be meaningfully asserted by a script.

- `ara/` is the current reference state — built entirely by actually running a
  prompt below through the real skill, not hand-written.
- `prompts/<skill>-trajectory.md` — a stable prompt that replays a real research
  trajectory through that skill's full pipeline, end to end, against `ara/`.

Right now there's one prompt: `prompts/research-manager-trajectory.md` replays the
ResNet paper's own research narrative through `research-manager`'s full four-stage
pipeline (Context Harvester → Event Router → Maturity Tracker → Logic Layer
Reconciliation), plus its taste-comment capability. When testing touches a
different skill, add another `prompts/<skill>-trajectory.md`.

**This doesn't generalize to every skill unchanged — read this before adding a
second prompt:**

- **Write-incremental skills** (research-manager today; maybe others later) fit
  the current pattern directly: replay a real trajectory against the shared `ara/`,
  let the skill build it up turn by turn, and commit the result.
- **Read-only skills** (`rigor-reviewer`, `research-visualizer`,
  `research-foresight`) can safely use the same `ara/` as input — they never
  mutate it — but the thing to demonstrate is the skill's *output* (does the
  review/visualization/answer look right), not a diff of `ara/`.
- **`compiler` doesn't fit this pattern at all.** It builds an ARA from a paper
  or repo rather than editing an existing one, so there's no shared `ara/` to
  test it against — it needs its own fixture (a sample paper/repo input plus
  human review of the ARA it produces).

Whenever you change something a prompt here depends on, copy that prompt into
your agent, read the diff/output it produces, and — if the routing/staging/
crystallization decisions throughout look right — commit the updated `ara/` as
part of your PR. The reference ARA in this repo is therefore always whatever the
most recent contributor's real run produced.

## Provenance

`ara/` was built by actually running `prompts/research-manager-trajectory.md`
once against a real, source-cited research narrative: the paper "Deep Residual
Learning for Image Recognition" (He et al., 2015) narrates its own research
process in §1/§3/§4 — noticing a depth-induced degradation problem, ruling out
two explanations, reformulating the approach, validating it, then scaling it —
and every event in the resulting `trace/exploration_tree.yaml` (`N01`-`N15`) and
every claim/heuristic in `logic/` traces back to a specific section, table, or
figure in that narrative (see the `Sources`/`Proof`/`evidence` pointers inline).
Nothing about *what happened* is invented — only the turn-by-turn framing (how an
already-real event maps onto research-manager's own event types) is something
this run constructed, and `trace/pm_reasoning_log.yaml` documents that reasoning
turn by turn.

`N16` and the entries in `trace/taste_log.yaml` are different in kind from
everything else here: they're the live reactions of whoever actually ran this
test, generated fresh at test time — that's inherent to what a taste comment is,
not an exception to the "don't invent the trajectory" rule (there's no historical
"researcher reaction" to source, because the reaction only exists once someone
uses the capability).

This reuses the same underlying paper as `examples/resnet-ara-example`, but is a
separate, from-scratch build via `research-manager`'s own pipeline rather than a
copy of that compiler-generated artifact — the two demonstrate different skills
and shouldn't be conflated. (Earlier versions of this demo pre-seeded `ara/`
directly from `resnet-ara-example`'s content and only exercised the taste-comment
capability against it; that undersold what "testing the skill" should mean — see
the PR history for why this version replays the full pipeline from scratch instead.)

## What to actually check when reviewing a run

There's no automated checker here — read `ara/` and judge it directly. In
particular:

- `trace/pm_reasoning_log.yaml` and `trace/sessions/2026-07-27_001.yaml` — the
  routing/closure-signal judgment calls made turn by turn, including near-misses.
  Do these decisions look right? Would you have routed/crystallized differently?
- `logic/claims.md` / `logic/solution/heuristics.md` — do the crystallized
  entries read as sound, falsifiable, correctly scoped?
- `trace/taste_log.yaml` and the `Taste` subsections in `logic/` — do the tag
  choices (attitude, object-of-judgment) match what the comment text actually says?
- `trace/exploration_tree.yaml` — are dead ends, decisions, and the one pivot
  classified as the right node type; do `also_depends_on` links make sense?

This is inherently subjective, and that's the point — a skill change that makes
research-manager's outputs on this trajectory look worse to a human reader is a
regression, whether or not it breaks anything a script could check.
