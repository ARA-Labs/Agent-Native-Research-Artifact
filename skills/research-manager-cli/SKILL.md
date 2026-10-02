---
name: research-manager-cli
description: |
  End-of-turn research process recorder with progressive crystallization. Invoked at the END of
  EVERY turn, after the user's current request has been fully addressed and before yielding control
  back to the user. Reviews what happened in the turn, extracts research-significant events, and
  writes them into the ara/ artifact through a three-stage pipeline: Context Harvester → Event
  Router → Maturity Tracker. Trace events (decisions, experiments, dead ends, pivots) are recorded
  immediately as journey facts. Knowledge events (claims, heuristics, concepts, constraints) are
  staged first and crystallize into typed layers ONLY when closure signals appear — topic
  abandonment, verbal affirmation, empirical resolution, or artifact commitment. NEVER mid-turn.
  All entries carry provenance tags (user / ai-suggested / ai-executed / user-revised).
  Also supports optional, user-triggered taste comments — free-form evaluative reactions to a
  claim, heuristic, or trace node — independent of the crystallization pipeline.
user-invocable: true
argument-hint: "[optional: hint about what happened this turn]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ara *)
metadata:
  author: ara-commons
  version: "2.6.0"
  tags: [research, process-recording, provenance, progressive-crystallization, knowledge-management, taste-comments]
---

# Live Research Project Manager (Live PM)

## CLI-only access boundary

Every knowledge-layer or root `PAPER.md` read/write in this page uses `ara -C <artifact>`; the
words read, open, search, write, append and edit retain their original procedural meaning,
but never authorize direct knowledge-file tools. For complete source use
`show --document <native-path> --source --full --json` (exact content and SHA-256 digest);
`ls`, `find`, `path`, `refs`, `open` and `status` are access aids, not semantic judgments.
Source/evidence bodies and skill pages remain direct only within the baseline scope.
No direct fallback, automatic semantic retry, new role, or altered stopping rule is allowed.
The entrypoint loads `references/cli-access.md` directly for executable wire details.
Pending protocol review and binary proof remain visible in the variant lock.


You are the Live PM. You run a per-turn epilogue that captures research activity into the
`ara/` artifact while honoring the principle of **progressive crystallization**: forcing
premature structure distorts the record. Most observations are staged and only mature into
formal entries when externally observable closure signals indicate the researcher has
treated them as settled.

Load `references/cli-access.md` directly before knowledge access; and load every
supplied reference directly from this entrypoint when applicable:
- `references/schema-and-initialization.md` — full directory/schema/initialization source.
- `references/event-taxonomy.md` — original classification, provenance and forensic binding.
- `references/taste-comments.md` — original taste trigger/target/confirmation.
- `templates/reader-report.md` — unchanged reader-report input shape.

## Layer Mutability

The artifact has two mutability regimes. Honor them strictly.

- **`ara/logic/` is mutable** — it is the *current best understanding* of the project, a
  clean specification of what we currently believe. Stage 4 reconciles it freely with new
  evidence: rewriting statements, flipping status, splitting/merging claims, repairing
  dependencies, fixing terminology. The logic layer carries NO history of its own — each
  entry is a present-state snapshot plus a `Last revised` pointer back to the trace.
- **`ara/trace/` and `ara/staging/` are append-only and immutable** — they are the
  journey record. New entries are appended; existing entries are NEVER edited except to
  set forward-reference pointers (e.g. flipping a staged observation's `promoted: false`
  → `true` plus `promoted_to: logic/claims.md:C07`, or appending to a session record's
  events for the current turn). Prior entries' content is never rewritten. The trace is
  how we recover history that the logic layer intentionally discards.

This split lets `claims.md` read as a clean specification while preserving full
provenance and revision history in the trace.

## When This Skill Runs

- **NEVER mid-turn.** Do not read or write `ara/` while still working on the user's request.
- **ALWAYS at end of turn.** After the user's request is fully addressed and before yielding,
  run the epilogue.
- **Per-turn cadence.** A turn = one user message + the agent's response (including tool
  calls). The skill fires once per turn.
- **Sessions are calendar-day groupings.** One session record file per day; turns within
  the same day append to it.
- **Skip empty turns.** Greetings, acknowledgments, clarifying questions with no new
  information, pure formatting — produce no record.

## The Four-Stage Pipeline

```
┌──────────────────┐  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────────┐
│Context Harvester │->│ Event Router │->│ Maturity Tracker │->│  Logic Layer         │
│ (extract what    │  │ (classify +  │  │ (crystallize on  │  │  Reconciliation      │
│  happened)       │  │  route)      │  │  closure signal) │  │  (reconcile current  │
│                  │  │              │  │                  │  │   state w/ this turn)│
└──────────────────┘  └──────────────┘  └──────────────────┘  └──────────────────────┘
```

### Stage 1 — Context Harvester

Scan THIS TURN only (the user's most recent message + your tool calls and results since the
previous epilogue). Identify research-significant activity in two categories:

- **AI actions performed**: experiment runs, code edits, file creations, commands,
  literature searches, benchmark numbers.
- **Researcher directions** expressed or confirmed: hypotheses, design choices, abandoned
  approaches, questions, affirmations, revisions.
- **Reader reports** (cross-agent feedback): structured `contradiction_report`s produced against
  this ARA by a reader engine (e.g. `research-foresight` PREDICT §7) and supplied as input this
  turn — open `reader-report` issues on the ARA's repository, or report files handed to this run
  (shape: `templates/reader-report.md`). Each is a candidate event, NEVER an edit to apply.

Output a flat list of candidate events with raw context.

### Stage 2 — Event Router

For each candidate, classify it, tag provenance, distill the payload, and route it. The
routing dichotomy is: **journey facts go direct; interpretive claims go staged.**

→ Use `references/event-taxonomy.md` for: kind classification, the direct-vs-staged
decision tree, the skip filter, provenance assignment, ID conventions, and forensic
binding requirements.

Distill conversational prose into telegraphic, quantitative language before writing.

### Stage 3 — Maturity Tracker

Walk `staging/observations.yaml` and decide which staged observations are mature. **Maturity
is the presence of a closure signal, not a counter and not an LM judgment.**

#### Closure signal taxonomy

A staged observation crystallizes when **at least one** of these signals is present:

1. **Topic abandonment** — observation's topic has no events in the last `k=5` turns AND
   `open_threads` does not reference it. Match topic by `bound_to` exploration nodes or by
   key nouns/identifiers in `content`. Be generous about what counts as a revisit — false
   abandonment is worse than late abandonment.

2. **Verbal affirmation** — the user explicitly endorsed the observation in this turn:
   "yes" / "confirmed" / "correct" / "let's go with X" / "ship it" / "exactly". The
   adoption must be FIRST-PERSON. Silence is not affirmation. "Maybe" / "probably" is not
   affirmation.

3. **Empirical resolution** — an experiment in the observation's `bound_to` produced a
   result and the researcher commented on it. **If the experiment refutes the observation,
   promote to a `dead_end` node, NOT to a `claim`.** The observation is closed either way.

4. **Artifact commitment** — a downstream artifact now depends on the observation: a
   `decision` node cites it as evidence, a config got fixed to a value it specifies, code
   was merged that depends on it, or a subsequent claim cites it as a premise.

**Default to non-promotion.** If no signal is clearly present, leave it staged. Premature
crystallization is the failure mode this design exists to prevent.

#### Crystallization procedure

When a signal fires for `O{XX}`:

1. Read O{XX}'s `content`, `context`, `potential_type`, `provenance`, `bound_to`.
2. Read the target layer through ara first; let the corresponding add/promote operation allocate the next ID and consume its result/bindings.
3. Construct a typed entry using the schema (see Schemas below). **Before any number enters a
   `Statement`/`Rationale`, ground it per "Number grounding" below — open the source, copy the
   matched line verbatim into `Sources`, then write the number as a copy of that quote.** Carry
   forward `provenance`. Verbal-affirmation upgrades `ai-suggested` → `user-revised` (or `user` if
   reproduced verbatim). The other three signals do **not** upgrade provenance.
4. Add fields: `Crystallized via: <signal>`, `From staging: O{XX}`.
5. Establish forensic bindings (claim→proof, heuristic→code, decision→evidence). Use
   `[pending]` + TODO if a binding cannot be made now.
6. Update O{XX}: `promoted: true`, `promoted_to: <layer>:<id>`, `crystallized_via: <signal>`.
   **Do not delete the observation** — the trail from raw to typed is part of the record.

#### Number grounding (claims & heuristics)

Every load-bearing number in a `Statement` (or a heuristic's `Rationale`/`Sensitivity`/`Bounds`)
is grounded the way code is — transcribed from an open source, never written from memory:

1. **Open before you write.** Before the number enters the prose, open its source and copy the
   matched line *verbatim* into `Sources` (`<value> ← <source ref> «matched line» [input|result]`).
   The number you then write in the prose is a copy of the value inside that quote — not a value
   recalled and back-cited. An entry with a bare path and no «quote» is invalid.
2. **Input vs result.** Tag each entry `[input]` (a value you set — cite the source that defines it)
   or `[result]` (a value the run produced — cite the log/output that reports it). Don't cite a
   measured outcome to the config meant to produce it, or vice versa.
3. **No inheritance.** Re-open *this* claim's own source for every number; a value shared with a
   dependency claim is re-verified here, never copied from the dependency's wording.
4. **`[pending]` beats a guess.** Can't open or locate a source this turn? Write
   `<value> ← [pending: what's missing]`. An unverified-but-plausible path is fabrication and is
   worse than `[pending]`.

#### Contradiction trigger

When a new event contradicts something already staged or crystallized:

- **Do not silently overwrite either entry.**
- Flag both with `<!-- CONFLICT: see {other-id} -->` (or `# CONFLICT:` in YAML).
- Append an `unresolved` `decision` node to the exploration tree referencing both, with
  provenance reflecting who introduced the contradiction.
- Stop. Adjudication is the researcher's job at a future turn.

#### Reader reports (cross-agent feedback)

Reader reports are **adjudicated by this manager in the turn they arrive** — every report leaves
the turn with a verdict. This is the one sanctioned exception to the contradiction trigger's defer
rule, scoped to reader reports only (the manager's own mid-research contradictions still defer as
above). A report targeting nothing in `logic/` is simply staged as an ordinary observation
(`provenance: ai-suggested`, report ref recorded in `context`). For a report targeting a
crystallized entry:

1. **Verify.** Resolve the report's `basis` refs and re-read the targeted entry. The report is
   **upheld** only when evidence resolvable *inside the ARA* (trace nodes, evidence files, session
   records) corroborates the observation and genuinely contradicts the cited clause. Reader-side
   pointers the manager cannot resolve are recorded but do not count toward upholding.
2. **Upheld** → fold the correction in as a Stage 4 content revision: edit the entry (provenance
   `ai-suggested`, report ref recorded), record full before/after under `logic_revisions:`, and
   append a `decision` node (`status: resolved`) referencing both the entry and the report. Status
   changes follow the ordinary transition rules — an upheld report counts as empirical resolution.
3. **Rejected** — resolvable evidence positively shows the report wrong (does not support the
   observation, or does not contradict the clause) → the entry is untouched; append a `decision`
   node (`status: resolved`) recording the verdict and its specific reason.
4. **Unverifiable** — the ARA contains nothing that can corroborate *or* refute the observation
   (a report resting only on reader-side pointers) → do NOT close it as rejected: this one case
   falls back to the defer rule above. Flag the entry (`<!-- CONFLICT: see reader-report <ref>
   -->`) and append an `unresolved` `decision` node referencing both, carrying the report's
   `repro` for a future run to execute. A possibly-true dispute stays visible on the entry rather
   than dying in the session record.
5. **Notify, don't wait.** In every case the human receives an after-the-fact summary: the verdict
   and its grounds go into the session record and the turn's `[PM]` summary line (e.g.
   `reader-report on C02 upheld → Conditions revised`; `reader-report on C04 rejected:
   evidence does not contradict clause`; `reader-report on C07 unverifiable → CONFLICT flagged,
   repro preserved`). The manager reaches a verdict every time.

The single-writer rule is unchanged: readers never write the ARA — this manager is the only
writer, and a report is INPUT to it, not an edit.

#### Stale-flagging

A staged observation that has neither been promoted nor referenced for **3+ session-days**
gets `stale: true`. Stale observations are surfaced at the next briefing for the
researcher to triage — the manager does not auto-discard.

### Stage 4 — Logic Layer Reconciliation

Reconcile `logic/` (the current best understanding) with this turn's events so it stays
internally consistent and faithful to present evidence. Operates only on **already-crystallized**
entries — staged observations belong to Stage 3. (History lives in the trace; see Layer Mutability.)

#### What Stage 4 may do

1. **Status updates** — flip a claim's `Status` field when evidence warrants.
2. **Content revisions** — rewrite a `Statement`, `Rationale`, or definition when new
   evidence narrows scope, terminology changed, or wording no longer matches what's
   actually supported. Keep `Statement` a generalized mechanism/relationship and sharpen
   `Conditions` as the regime becomes clearer; new run numbers update `Proof`/`evidence`,
   never the Statement. A rewrite re-grounds every number it now contains (Number grounding);
   any changed value gets its own fresh `Sources` «quote», never a carried-over one.
3. **Structural changes** — split a claim into two, merge duplicates, repair
   dependencies, rename ids when concepts are renamed. Also **generalize**: when several
   crystallized claims are together evidence for a more general relationship none states
   alone, author a new claim whose `Dependencies` are those narrower claims and whose
   `Proof` spans their evidence — keep the narrower claims in place; the new claim sits
   above them, not instead of them (only when a signal this turn makes the relationship
   evident — never a routine sweep).
4. **Consistency pass** — scan for broken cross-references (claim cites C05 which no
   longer exists), terminology mismatch with `concepts.md`, dependency loops.

#### Allowed status transitions

```
hypothesis ──► testing ──► supported
     │            │            ▲
     │            └──► weakened┘
     ├────────────────► refuted    (terminal, empirical)
     ├────────────────► withdrawn  (terminal, non-empirical)
     └─ any ─────────► revised    (Statement rewritten; reset to testing/hypothesis)
```

- `hypothesis`: just crystallized; no evidence gathered yet (default for new claims)
- `untested`: deliberately deferred — work not started, not currently planned
- `testing`: an experiment that bears on the claim is in progress
- `supported`: empirical evidence confirms the claim
- `weakened`: evidence is mixed, partial, or weaker than required
- `refuted`: empirical evidence disproves — **terminal**
- `withdrawn`: researcher dropped the claim for non-empirical reasons (pivot, scope cut) — **terminal**
- `revised`: a transition marker, not a resting state — after recording the revision in
  the trace, the claim's `Status` settles to `testing` if prior evidence still applies,
  else `hypothesis`

`refuted` and `withdrawn` are terminal unless the user explicitly revives the claim (in
which case route through `revised`).

#### Reconciliation signals

For each crystallized entry in `logic/`, check this turn for:

1. **Empirical resolution** — an experiment in the entry's `Proof` refs or `bound_to`
   nodes produced a result this turn AND the researcher commented on it.
   - Result confirms → `supported` (or one step toward it)
   - Result partial / narrower than claim → `weakened`, and consider rewriting the
     `Statement` to match the actual scope supported
   - Result disproves → `refuted` AND append a `dead_end` node referencing the claim
2. **Verbal declaration** — first-person, explicit, naming the claim or unambiguously
   referring to its content. Covers status ("C07 confirmed" / "drop C07"), revisions
   ("C07 should really say X"), and structural changes ("split C07 into two — one for
   training, one for inference"). Hedged language ("maybe", "looks like") does NOT trigger.
3. **Dependency change** — a claim this entry depends on changed status or was rewritten.
   Examples: a premise was refuted → review entries that cited it; a referenced concept
   was renamed → update the wording.
4. **Artifact commitment** — code/config merged this turn explicitly depends on the entry.
   Upgrades `hypothesis` → `testing` (the commitment IS the test); does NOT reach
   `supported` alone.
5. **Terminology drift** — a new concept added to `concepts.md` this turn refines or
   renames a term the entry uses. Update the wording for consistency.
6. **Contradicting evidence** — new evidence contradicts an entry's current content or
   status. **Do not auto-overwrite.** Follow the Stage 3 contradiction trigger: flag
   both, append `unresolved` decision node, defer.

#### Edit procedure

When a signal fires for entry `E` (claim, heuristic, or concept):

1. Use `logic.revise` through `ara apply` for the affected fields in the logic file. **Overwrite the prior value** —
   the logic file is a current-state snapshot, not a redlined draft.
2. Update `- **Last revised**: YYYY-MM-DD (turn-id)` on the entry.
3. For status flips, also update `- **Status**:` to the new value.
4. If transitioning to `refuted`, ensure a `dead_end` node exists in
   `exploration_tree.yaml` referencing the entry (create one if not).
5. For structural changes:
   - **Split**: keep the original id pointing to the narrower/primary claim, allocate a
     new id for the spin-off, update all cross-references.
   - **Merge**: keep the lower id, mark the higher id as `withdrawn` with
     `Merged into: C{XX}`, redirect cross-references.
   - **Generalize**: allocate a new id for the more general claim, set its `Dependencies`
     to the narrower claims, and leave those claims in place (they remain its grounding).
6. **Record full before/after in today's session record** under `logic_revisions:`
   (see schema below). This is the ONLY place the prior wording is preserved — the
   logic file does not keep it.
7. Add a one-line note to `pm_reasoning_log.yaml` explaining which signal fired AND any
   signal you considered but rejected (near-misses are the most useful continuity record).

#### Provenance for revisions

- User dictated exact wording → `provenance: user`
- User said "revise C07 to mean X" without exact wording → `provenance: user-revised`
- Stage 4 reconciled autonomously (terminology, dependency repair, narrowing) →
  `provenance: ai-suggested`. The researcher can revert at any future turn by saying so.

#### Conservatism rules

- **Default to no change.** Reconciliation is allowed but not required. Don't churn the
  logic layer; only act when a signal demands it.
- **One-step transitions preferred.** Jumping `hypothesis` → `supported` in a single
  turn requires BOTH empirical resolution AND verbal affirmation in the same turn.
- **Terminal states require explicit signals.** Never reach `refuted` or `withdrawn` by
  inference from silence or staleness.
- **Never demote `supported` → `weakened`** on a single new event — flag as
  contradiction instead and let the researcher adjudicate.
- **Content rewrites preserve falsifiability.** A revised `Statement` must remain a
  falsifiable assertion with intact `Falsification criteria`. If the revision makes the
  claim un-falsifiable, flag for the researcher rather than rewriting silently.
- **Structural changes touching 3+ entries** (large refactors) — flag and defer to the
  researcher unless explicitly requested. Small refactors (rename one term across two
  claims) are fair game.
- **Log near-misses.** If you considered a signal but rejected it (hedged affirmation,
  ambiguous reference, result that touches a neighboring entry), record it in
  `pm_reasoning_log.yaml`.

## Per-Turn Procedure

```
1. Read existing ara/ knowledge with ara full source shows (current state); use CLI allocation/results for new IDs.
2. Stage 1 — harvest this turn's candidate events.
3. Stage 2 — classify/route each (per event-taxonomy.md): journey facts direct to trace/; interpretive events staged to staging/observations.yaml.
4. Stage 3 — crystallize staged observations whose closure signal fired; flag contradictions; mark 3+-day-idle observations stale.
5. Stage 4 — for each crystallized logic/ entry, apply status/content/structural edits when a signal fires; run the cross-ref consistency pass; record before/after in the session record; log near-misses.
6. Use one ara apply batch: session.log appends complete turn arrays and audited rolling metadata/index; record.append appends the complete PM reasoning notes.
7. Print one-line summary, e.g.:
     [PM] Turn captured: 1 decision (direct), 2 observations staged, 1 claim crystallized via affirmation, C03 testing→supported, C07 revised (scope narrowed).
   Or, for empty turns:
     [PM] Turn skipped: no research events.
```

## Schemas and Initialization

Load `references/schema-and-initialization.md` directly for the complete source directory
structure, every schema, and the unchanged initialization trigger/seed set. Read it before
constructing any record or first artifact; no fields or history instructions are omitted.

## Briefing (fresh conversation only)

On the first turn of a new conversation (not every turn), silently read:
- latest session record's `summary`, `open_threads`, `ai_suggestions_pending`, `key_context`
- `claims.md` status counts
- `staging/observations.yaml` non-stale, non-promoted entries (especially those near closure)
- `pm_reasoning_log.yaml` last few entries (organizational continuity)

Surface relevant pieces only when they bear on the user's first task — never lead with a
formal briefing the researcher did not ask for. If the user asks "where did we leave off",
deliver the full briefing.

## Taste Comments (optional, user-triggered)

Separate from the four-stage pipeline above. When the user reacts evaluatively to a specific
claim, heuristic, or trace node this turn, record it as a taste comment: always
`provenance: user`, never staged, never affects `Status` or crystallization. Every taste
comment carries both an attitude (`endorse | uncertain | reject`) and an object of judgment
(`claim | evidence | framing | priority`) — the two are independent axes, not one label. →
Use `references/taste-comments.md` for trigger detection, target resolution, the
confirm-before-write procedure, and the tag rules; schemas above.

Taste is additive, never a substitute for the normal pipeline: if the same utterance also
introduces new research content, that content is routed through Stage 1–4 as its own event
regardless of the taste comment (see `references/taste-comments.md`).

Runs inline within the normal epilogue when triggered — not a separate interactive prompt, and
not asked about on turns where it doesn't come up.

## Rules

1. **End-of-turn only; never mid-turn.** Skip empty turns (greetings, ack, formatting).
2. **Never fabricate.** Log only what actually happened or was discussed.
3. **Stage interpretive events by default; crystallize only on a closure signal** — abandonment / affirmation / resolution / commitment. No counters, no LM-judged maturity.
4. **Never auto-upgrade provenance.** `ai-suggested` holds until explicit user affirmation.
5. **Stage 4 defaults to no change.** Edits require an explicit signal this turn; terminal states (`refuted`/`withdrawn`) need explicit triggers, never silence/staleness. Log near-misses.
6. **Respect layer mutability** (see top): `logic/` overwrites in place; `trace/` and `staging/` are append-only except forward-reference pointers. Every logic edit gets a `logic_revisions:` before/after in the session record — the only place pre-edit content is kept.
7. **Never silently overwrite contradictions** — flag both, append an `unresolved` decision node, defer.
8. **Read target files first through ara** (no dupes; CLI assigns new IDs); establish forensic bindings (claim→proof, heuristic→code, decision→evidence), `[pending]`+TODO if not yet bindable. Keep YAML valid; summary line terse.
9. **Taste comments never guess.** Confirm the target before writing (see references/taste-comments.md); claim/heuristic taste is inline, trace-node taste goes to `taste_log.yaml` and never edits the node.
