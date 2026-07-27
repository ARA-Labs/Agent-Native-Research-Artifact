# Taste-Comment Smoke Test Prompt

Copy everything below the line into your agent, in a checkout of this repo, whenever
you've changed anything `research-manager`'s taste-comment capability depends on
(`skills/research-manager/SKILL.md`, `skills/research-manager/references/taste-comments.md`,
or `skills/research-manager/references/event-taxonomy.md`). It doesn't hardcode which
elements to react to — it reads whatever is currently in the reference ARA, so it stays
usable as that ARA evolves.

---

You are acting as the `research-manager` skill's taste-comment capability. Read
`skills/research-manager/references/taste-comments.md` and the Claim / Heuristic / Taste
Log schemas in `skills/research-manager/SKILL.md` — that is the current spec, not this
prompt; follow whatever it currently says even if it has changed since this prompt was
written.

The reference ARA is at `examples/skills-test-demo/ara/`. Read its
`logic/claims.md`, `logic/solution/heuristics.md`, and `trace/exploration_tree.yaml`.

Simulate a researcher reviewing this ARA and reacting to it out loud. Invent 2–3 reactions
to *real* elements already present in the ARA (not elements you make up), covering:

- At least one claim and one heuristic or trace node, so both write paths get exercised.
- A mix of attitudes (`endorse | uncertain | reject`) and objects of judgment
  (`claim | evidence | framing | priority`) — don't make every reaction the same tag.
- At least one reaction that, in addition to being a judgment, also contains an
  actionable suggestion (a proposed next step, a correction, a new question) — so the
  taste/pipeline co-firing rule gets exercised, not just the taste write on its own.

For each reaction, follow the spec's target-resolution and confirm-before-write procedure
as written, then apply the write. Do not skip straight to writing — narrate which element
you resolved each reaction to and why, the same way the live skill would confirm before
writing.

When done, show a diff of everything you changed under `examples/skills-test-demo/ara/`
and a one-line summary of each reaction (target, attitude, object, and whether it also
triggered a pipeline event).

If the result looks correct — the invariants hold and the output reads like something the
spec actually intends — commit the updated `ara/` as part of your PR, so the reference ARA
in this repo reflects the current skill's behavior. If something looks wrong, that's a bug
in the skill change you're testing, not in this prompt or the ARA.

Then run `node examples/skills-test-demo/checks/research-manager-taste-comments.mjs` from the repo root and
paste its output — it diffs the current `ara/` against the version at `origin/main` and
asserts the structural invariants a taste write must never break (tag/object enums,
append-only-ness, trace nodes never mutated, targets resolving to real nodes, `T` ids
unique and sequential).
