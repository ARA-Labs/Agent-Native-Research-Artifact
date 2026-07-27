# ARA Skills Test Demo

A living regression example, shared across the ARA skills. Contributors run this
locally — no CI wiring, no install step, no API key.

## How this works

One shared `ara/`, exercised by any number of skill-specific prompts. Each prompt
demonstrates that skill's **entire** pipeline working end-to-end on a real research
trajectory — not just one capability in isolation — because the primary judgment on
whether a skill change is good is a human reading the resulting ARA, which is
inherently subjective and can't be meaningfully asserted by a script.

- `ara/` is the current reference state — built entirely by actually running a
  prompt below through the real skill, not hand-written.
- `prompts/<skill>-trajectory.md` — a stable prompt that replays a real research
  trajectory through that skill's full pipeline, end to end, against `ara/`.
- `checks/<skill>-<thing>.mjs` — a *supporting* mechanical check for the one part
  of a run's output that IS assertable without a human reader (e.g. tag enums,
  append-only-ness). It is not a pass/fail gate on the run as a whole.

Right now there's one pair: `prompts/research-manager-trajectory.md` replays the
ResNet paper's own research narrative through `research-manager`'s full four-stage
pipeline (Context Harvester → Event Router → Maturity Tracker → Logic Layer
Reconciliation), plus its taste-comment capability; `checks/research-manager-taste-comments.mjs`
is the supporting check for the taste-comment portion of that run. When testing
touches a different skill, add another `prompts/<skill>-trajectory.md` (and a
`checks/*.mjs` only for whatever part of its output is actually assertable).

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

## What `checks/research-manager-taste-comments.mjs` asserts

Diffing the current `ara/` against its state at `origin/main`:

1. Every claim/heuristic entry present at `origin/main` still has all of its
   non-Taste fields byte-identical now — a taste write touches nothing but the
   `Taste` subsection.
2. Any taste bullet already present at `origin/main` is still present,
   unchanged, at the same position now — taste is append-only.
3. Every taste bullet's attitude tag is one of `endorse | uncertain | reject`.
4. Every taste bullet's object-of-judgment tag is one of
   `claim | evidence | framing | priority`.
5. Every trace node present at `origin/main` is byte-identical now — trace
   nodes are pointed at, never edited. New nodes may be appended (e.g. by the
   taste/pipeline co-firing rule) without failing this check.
6. Every `trace/taste_log.yaml` entry's `target` resolves to a real node id in
   the current `trace/exploration_tree.yaml`.
7. `trace/taste_log.yaml` entry ids are unique and sequential from `T01`.

Run it with:

```
node examples/skills-test-demo/checks/research-manager-taste-comments.mjs
```

It accepts optional `[araDir] [gitRef]` arguments if you want to point it
somewhere other than `ara/`/`origin/main`.

## Scope

`checks/research-manager-taste-comments.mjs` validates structural invariants for
the taste-comment portion of a run only — it says nothing about whether the
routing/staging/crystallization decisions across the rest of the trajectory
(which experiment triggered which claim's crystallization, whether a dead end
was classified correctly, whether a closure signal actually fired) were the
right calls. That's the part a human reading `ara/` and
`trace/pm_reasoning_log.yaml` has to judge — it's inherently subjective and this
repo doesn't pretend a script can substitute for that read.
