# Taste-Comment Invariant Fixture

A regression fixture + checker for the taste-comment capability added to
`research-manager` (see `skills/research-manager/references/taste-comments.md`).
Collaborators changing that skill can run this locally — no CI wiring, no
install step, no API key.

## What's in here

- `before/` — a real, verbatim subset of `examples/the-ara-of-ara` (an actual
  multi-week live-session ARA elsewhere in this repo): claim `C06`, heuristic
  `H04`, and trace node `N21` (a real nanoGPT RL-finetuning RE-Bench run), each
  copied unmodified from their source files. This is deliberately **not**
  synthetic content — the whole point of a regression fixture for a
  taste-comment write is that it exercises real prose, not a hand-crafted
  toy claim.
- `after/` — the same three entries with taste comments applied by hand,
  following `taste-comments.md` verbatim, plus one addition: the simulated
  reaction to `N21` intentionally carries *both* a judgment (`reject` /
  `priority`) *and* an actionable suggestion, so the fixture also exercises
  the taste-and-pipeline co-firing rule — the suggestion shows up as a new
  `N22` question node in `after/trace/exploration_tree.yaml`, appended
  alongside the untouched `N21`, exactly as the spec now requires.
- `check.mjs` — a dependency-free Node script that diffs `before/` against
  `after/` and asserts the invariants a taste write must never break.

`logic/experiments.md` is intentionally absent: research-manager has no write
path into that file at all (it's compiler-owned), so there's nothing on that
axis for a taste-comment regression test to check.

## What `check.mjs` asserts

1. Every claim/heuristic present in `before/` still has all of its non-Taste
   fields byte-identical in `after/` — a taste write touches nothing but the
   `Taste` subsection.
2. Any taste bullet already present in `before/` is still present, unchanged,
   at the same position in `after/` — taste is append-only.
3. Every taste bullet's attitude tag is one of `endorse | uncertain | reject`.
4. Every taste bullet's object-of-judgment tag is one of
   `claim | evidence | framing | priority`.
5. Every trace node present in `before/trace/exploration_tree.yaml` is
   byte-identical in `after/` — trace nodes are pointed at, never edited.
6. Every `trace/taste_log.yaml` entry's `target` resolves to a real node id
   in `after/trace/exploration_tree.yaml`.
7. `trace/taste_log.yaml` entry ids are unique and sequential from `T01`.

## Running it

```
node examples/nanogpt-taste-fixture/check.mjs
```

Exits 0 and prints `PASSED` when every invariant holds; exits 1 and lists
each violation otherwise. It also accepts two directory arguments
(`node check.mjs <before> <after>`) if you want to point it at a different
before/after snapshot pair — e.g. a real research-manager run's output,
once one exists — rather than this fixture's `before/`/`after/`.

## Scope

This checks structural invariants only — it does not (and, since
research-manager is an LLM-driven skill rather than a deterministic parser,
cannot) assert that a real research-manager run would produce this exact
`after/` wording. What it catches is regressions in the *shape* of taste
writes: a schema change that lets an invalid tag through, a change that lets
a taste write leak into other fields, a change that breaks append-only-ness
on trace nodes, or a change that breaks the taste/pipeline co-firing rule.
