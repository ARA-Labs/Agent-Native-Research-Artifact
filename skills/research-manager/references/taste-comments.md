# Taste Comments

Canonical reference for the **Taste Comment** capability. Loaded on demand when a turn
contains one. SKILL.md owns the pipeline orchestration and schemas — this file covers
trigger detection, target resolution, and the confirm-before-write procedure.

A taste comment is the researcher's own evaluative reaction to a specific piece of
AI-produced research. It is **not** part of the crystallization pipeline: it never gets
staged, never crystallizes, never changes a `Status` or a `Provenance`, and it is always
`provenance: user` (the whole point is that it's the researcher's own take — the AI does
not write these on its own behalf). It is optional, additive, and can be skipped entirely
without affecting anything else in the artifact.

## When This Fires

Only when the user's message this turn expresses an evaluative reaction to an **identifiable**
element already in `logic/claims.md`, `logic/solution/heuristics.md`, or
`trace/exploration_tree.yaml` — the reaction must be traceable to one specific entry.

Does not fire for:
- General feedback about the conversation, the AI's tone, or process, with no research
  element as its target
- A reaction with no identifiable target — see Target Resolution below rather than
  guessing one

**Taste and new research content are not mutually exclusive — a single utterance is routed
as both when it contains both.** An evaluative reaction to an existing entry always fires
taste, regardless of whether the same utterance also introduces new research content (a
correction, a new claim, a proposed next step, a redirect). That new content is never
absorbed into the taste comment or left implicit in its free text — it independently goes
through the normal Stage 1–4 pipeline as its own candidate event (see SKILL.md and
`event-taxonomy.md`), exactly as it would if the taste reaction weren't there at all. Only an
utterance that is *purely* new research content, with no evaluative reaction attached, skips
taste entirely and goes through the pipeline alone.

## Target Resolution & Confirm-Before-Write

Never write a taste comment on a guess. Every write is confirmed first.

1. Search `claims.md`, `heuristics.md` (by title/content match), and
   `exploration_tree.yaml` nodes of type `experiment | decision | dead_end | pivot`
   (by title/content match) for what the user is referring to.
2. **Exactly one strong match** — state it back before writing: quote the entry's title
   (and, for claims/heuristics, the `Statement`/`Rationale` first clause) and confirm this
   is the target. Write only after the user confirms.
3. **No match, or multiple plausible matches** — do not guess. Ask the user to point at the
   right one (or give an id) rather than picking.
4. `question` nodes are not valid targets (they have no content yet to react to).

## Attitude Tag

Every taste comment carries exactly one attitude tag: `endorse | uncertain | reject`.

- Derive it from the user's own phrasing when the sentiment is unambiguous.
- If the sentiment is genuinely ambiguous, ask which of the three it is rather than
  guessing — a wrong tag is worse than a short clarifying question.
- There is no fourth "suggestion" tag, and none is needed: an actionable suggestion inside
  the reaction is not something the attitude tag needs to carry — it is routed through the
  normal pipeline per "When This Fires" above, on its own terms.

## Object of Judgment

Every taste comment also carries exactly one object tag, naming what the reaction is actually
about — the attitude tag alone conflates these:

- `claim` — whether the target's core assertion, choice, or conclusion is itself correct.
- `evidence` — whether what supports the target is sufficient or reliable, independent of
  whether the assertion itself is believed.
- `framing` — whether the target's premise, scope, or the question it set out to answer was
  posed correctly, independent of whether the conclusion reached within that framing holds.
- `priority` — whether the target was worth pursuing at all, relative to other work,
  independent of whether it is correct.

Derive it from the user's own phrasing when unambiguous; ask rather than guess when it
isn't — the same rule as the attitude tag.

## Write Procedure

Where it's written depends on the target's layer, because the two layers have different
mutability rules (see SKILL.md "Layer Mutability"):

- **Target is a claim or heuristic** (`logic/`, mutable) — append one bullet under that
  entry's `- **Taste**:` subsection (create the subsection if this is the entry's first
  taste comment). Never edit or remove a prior taste bullet. See SKILL.md Schemas for the
  exact line format.
- **Target is a trace node** (`trace/`, append-only/immutable) — do **not** edit the node.
  Append a new entry to `trace/taste_log.yaml` with `target: N{XX}` pointing back to it.
  This is the same pattern `staging/observations.yaml` uses to point at its crystallized
  destination (`promoted_to: logic/claims.md:C07`) without rewriting the original entry —
  taste comments on trace nodes follow that same append-a-pointer idiom instead of touching
  the immutable node.

Out of scope, both by explicit decision: `logic/experiments.md` (owned exclusively by the
compiler skill — research-manager has no write path into it at all, taste or otherwise) and
`logic/concepts.md` (definitional, not evaluative — no taste target there).

## ID Convention

`T{XX}`, global, assigned at write time (only `trace/taste_log.yaml` entries need one —
taste bullets under a claim/heuristic are inline and untracked, same as any other bullet in
that file). Read `trace/taste_log.yaml` first to find the highest existing `T` id.
