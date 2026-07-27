# ARA Skills Test Demo

A living regression example, shared across the ARA skills. Contributors run this
locally — no CI wiring, no install step, no API key.

## How this works

One shared `ara/`, tested by any number of skill/capability-specific
prompt+checker pairs:

- `ara/` is the current reference state — a small ARA anyone can read in a
  few minutes. It isn't scoped to any one skill; it's just a real, legible
  ARA that any skill can be exercised against.
- `prompts/<skill>-<capability>.md` — a stable, copy-pasteable prompt for one
  skill's capability. Copy it into your agent to exercise that capability
  against the current `ara/`.
- `checks/<skill>-<capability>.mjs` — a script that validates the result of
  running the matching prompt.

Right now there's one pair, `research-manager-taste-comments`, for
`research-manager`'s taste-comment capability (see
`skills/research-manager/references/taste-comments.md`). When testing
touches a different skill or capability, add another
`prompts/<name>.md` + `checks/<name>.mjs` pair.

**This doesn't generalize to every skill unchanged — read this before adding
a second pair:**

- **Write-incremental skills** (research-manager today; maybe others later)
  fit the current pattern directly: a prompt exercises the skill against the
  shared `ara/`, and the checker diffs `ara/` against a git ref the way
  `checks/research-manager-taste-comments.mjs` does.
- **Read-only skills** (`rigor-reviewer`, `research-visualizer`,
  `research-foresight`) can safely use the same `ara/` as input — they never
  mutate it — but their checker needs a different shape: validate properties
  of the skill's *output* (does the review/visualization/answer look right),
  not a diff of `ara/`, which won't have changed.
- **`compiler` doesn't fit this pattern at all.** It builds an ARA from a
  paper or repo rather than editing an existing one, so there's no shared
  `ara/` to test it against — it needs its own fixture (a sample paper/repo
  input plus an expected-shape check on the ARA it produces).

Whenever you change something a prompt here depends on, copy that prompt
into your agent, review the diff/output it produces, and — if it looks
right — commit the updated `ara/` (for write-incremental skills) as part of
your PR. The reference ARA in this repo is therefore always whatever the
most recent contributor's test run produced, one increment per PR that
touches a tested capability.

## Provenance

`ara/` was seeded from the **complete** `logic/claims.md` (all 8 claims),
`logic/solution/heuristics.md` (all 6 heuristics), and `trace/exploration_tree.yaml`
(all 15 nodes, across 5 node types — question, experiment, dead_end, insight,
decision) of `examples/resnet-ara-example` — not a hand-picked subset, so
there's no question of what got left out or why. The tree is flattened to
top-level nodes for legibility (in the source it's nested several levels deep
under `N01`/`N06`/`N13`); every `also_depends_on` cross-reference stays valid
since both ends of every reference are included. `C07`/`H04`/`N05` are the
same three elements used in the PR #32 review discussion. Any trace node id
≥ `N50` is demo-added by a taste reaction's co-fired pipeline event, never
present in the source artifact — there's no ambiguity between real and
generated content. None of this is synthetic content invented for the demo,
and `ara/` is deliberately kept separate from `resnet-ara-example/` itself so
this one can keep mutating without touching the compiler walkthrough that
example serves elsewhere. (Earlier versions of this demo tried
`examples/the-ara-of-ara` — too large/complex for a quick local read — then a
hand-picked subset of `resnet-ara-example` — too thin, and it invited the
question of why those particular elements were chosen.)

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

Each `checks/*.mjs` validates structural invariants only — it does not (and,
since these are LLM-driven skills rather than deterministic parsers, cannot)
assert that a real skill run would produce the exact wording in `ara/`. What
`checks/research-manager-taste-comments.mjs` catches is regressions in the
*shape* of taste writes: a schema change that lets an invalid tag through, a
change that lets a taste write leak into other fields, a change that breaks
append-only-ness on trace nodes, or a change that breaks the taste/pipeline
co-firing rule.
