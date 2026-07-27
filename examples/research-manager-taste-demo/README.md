# research-manager Taste-Comment Demo

A living regression example for the taste-comment capability in `research-manager`
(see `skills/research-manager/references/taste-comments.md`). Contributors run
this locally — no CI wiring, no install step, no API key.

## How this works

Unlike a frozen before/after fixture, this is **one ARA that keeps evolving**:

- `ara/` is the current reference state — a small ARA anyone can read in a minute.
- `prompt.md` is a single, stable prompt anyone can copy into their own agent to
  exercise the current taste-comment spec against the current `ara/`.
- `check.mjs` validates the result by diffing `ara/` against its state at
  `origin/main` (via `git show`) — no second copy of the ARA to keep in sync by hand.

Whenever you change anything the taste-comment capability depends on, copy
`prompt.md` into your agent, review the diff it produces under `ara/`, and — if
it looks right — commit the updated `ara/` as part of your PR. The reference ARA
in this repo is therefore always whatever the most recent contributor's test run
produced, one increment per PR that touches this capability.

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

## What `check.mjs` asserts

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
node examples/research-manager-taste-demo/check.mjs
```

It accepts optional `[araDir] [gitRef]` arguments if you want to point it
somewhere other than `ara/`/`origin/main`.

## Scope

This checks structural invariants only — it does not (and, since
research-manager is an LLM-driven skill rather than a deterministic parser,
cannot) assert that a real research-manager run would produce this exact
wording. What it catches is regressions in the *shape* of taste writes: a
schema change that lets an invalid tag through, a change that lets a taste
write leak into other fields, a change that breaks append-only-ness on trace
nodes, or a change that breaks the taste/pipeline co-firing rule.
