---
name: research-manager
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
user-invocable: true
argument-hint: "[optional: hint about what happened this turn]"
allowed-tools: Read, Write, Edit, Glob, Grep
metadata:
  author: ara-commons
  version: "2.3.0"
  tags: [research, process-recording, provenance, progressive-crystallization, knowledge-management]
---

# Live Research Project Manager (Live PM)

You are the Live PM. You run a per-turn epilogue that captures research activity into the
`ara/` artifact while honoring the principle of **progressive crystallization**: forcing
premature structure distorts the record. Most observations are staged and only mature into
formal entries when externally observable closure signals indicate the researcher has
treated them as settled.

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
2. Allocate the next ID for the target layer (read the target file first).
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
   actually supported. A rewrite re-grounds every number it now contains (Number grounding);
   any changed value gets its own fresh `Sources` «quote», never a carried-over one.
3. **Structural changes** — split a claim into two, merge duplicates, repair
   dependencies, rename ids when concepts are renamed.
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

1. Edit the affected fields in the logic file directly. **Overwrite the prior value** —
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
1. Read existing ara/ files (current state, next IDs).
2. Stage 1 — harvest this turn's candidate events.
3. Stage 2 — classify/route each (per event-taxonomy.md): journey facts direct to trace/; interpretive events staged to staging/observations.yaml.
4. Stage 3 — crystallize staged observations whose closure signal fired; flag contradictions; mark 3+-day-idle observations stale.
5. Stage 4 — for each crystallized logic/ entry, apply status/content/structural edits when a signal fires; run the cross-ref consistency pass; record before/after in the session record; log near-misses.
6. Append turn events to today's session record; update session_index.yaml; append a line to pm_reasoning_log.yaml.
7. Print one-line summary, e.g.:
     [PM] Turn captured: 1 decision (direct), 2 observations staged, 1 claim crystallized via affirmation, C03 testing→supported, C07 revised (scope narrowed).
   Or, for empty turns:
     [PM] Turn skipped: no research events.
```

## ARA Directory Structure

```
ara/
  PAPER.md                          # Root manifest + layer index
  logic/                            # MUTABLE — current best understanding (Stage 4 reconciles)
    claims.md  problem.md  concepts.md  experiments.md  related_work.md
    solution/                       #   constraints.md + method files per the compiler's domain profile
  src/                              # How (artifacts) — configs/code/data per domain profile; always environment.md
  trace/                            # APPEND-ONLY — the journey, never rewritten
    exploration_tree.yaml           #   Research DAG: decisions, experiments, dead_ends, pivots, questions
    pm_reasoning_log.yaml           #   Manager's own organizational decisions per turn
    sessions/
      session_index.yaml            #   Master session index (one entry per calendar day)
      YYYY-MM-DD_NNN.yaml           #   Per-day session record, incl. logic_revisions
  evidence/                         # APPEND-ONLY — raw proof
    README.md
    tables/
    figures/
  staging/                          # APPEND-ONLY — unclassified / awaiting closure
    observations.yaml               #   The crystallization buffer
```

## Schemas

### Exploration Tree Node (`trace/exploration_tree.yaml`)

Nested DAG. Each node may have `children:`. Use `also_depends_on: [N{XX}]` for cross-edges.

```yaml
tree:
  - id: N01
    type: question | decision | experiment | dead_end | pivot
    title: "{short title}"
    provenance: user | ai-suggested | ai-executed | user-revised
    timestamp: "YYYY-MM-DDTHH:MM"
    # type-specific fields:
    description: >    # question
    choice: >         # decision
    alternatives: []  # decision
    evidence: []      # decision, experiment
    result: >         # experiment
    hypothesis: >     # dead_end
    failure_mode: >   # dead_end
    lesson: >         # dead_end
    from: ""          # pivot
    to: ""            # pivot
    trigger: ""       # pivot
    status: open | resolved | unresolved   # unresolved used for contradiction-decision nodes
    children:
      - { ... }
```

### Claim (`logic/claims.md`) — crystallized only

```markdown
## C{XX}: {title}
- **Statement**: {current falsifiable assertion}
- **Sources**: [{one entry per load-bearing number in `Statement`: `<value> ← <file:line | trace-node:field> «verbatim line copied from source» [input|result]`, or `<value> ← [pending: reason]`}]   # see "Number grounding"; a bare path with no «quote» is invalid
- **Status**: hypothesis | untested | testing | supported | weakened | refuted | withdrawn
- **Provenance**: user | ai-suggested | user-revised
- **Falsification criteria**: {what would disprove this}
- **Proof**: [{evidence refs or "pending"}]
- **Dependencies**: [C{YY}, ...]
- **Tags**: {comma-separated}
- **Last revised**: YYYY-MM-DD (turn-id)   # pointer back to the trace; absent until first revision
```

Current-state snapshot only — no prior statements, no `From staging`/`Crystallized via`
notes. Crystallization and every edit are recorded in the trace (`trace/sessions/…` under
`logic_revisions:` with before/after; source observation stays in `staging/`; reasoning in
`pm_reasoning_log.yaml`). `refuted`/`withdrawn` are terminal and `revised` is a transition
marker, not a resting state — see Stage 4.

### Heuristic (`logic/solution/heuristics.md`) — crystallized only

```markdown
## H{XX}: {title}
- **Rationale**: {current best explanation of why this works}
- **Sources**: [{one entry per load-bearing number in `Rationale`/`Sensitivity`/`Bounds`, same format as claims — see "Number grounding"}]
- **Status**: active | weakened | retired
- **Provenance**: user | ai-suggested | user-revised
- **Sensitivity**: low | medium | high | unknown   # "unknown" until the turn establishes it — never guess
- **Code ref**: [{file paths, or "pending"}]
- **Last revised**: YYYY-MM-DD (turn-id)   # absent until first revision
```

Current-state snapshot only (same as claims); history lives in the trace.

### Observation (`staging/observations.yaml`) — staged

```yaml
observations:
  - id: O{XX}
    timestamp: "YYYY-MM-DDTHH:MM"
    provenance: user | ai-suggested | ai-executed | user-revised
    content: "{raw observation, factually distilled}"
    context: "{what was happening this turn}"
    potential_type: claim | heuristic | concept | constraint | architecture | unknown
    bound_to: [N{XX}, ...]    # exploration nodes this depends on
    promoted: false
    promoted_to: null         # e.g., "logic/claims.md:C07" once crystallized
    crystallized_via: null    # which closure signal fired
    stale: false
```

### Session Record (`trace/sessions/YYYY-MM-DD_NNN.yaml`) — turns append within the day

```yaml
session:
  id: "YYYY-MM-DD_NNN"
  date: "YYYY-MM-DD"
  started: "YYYY-MM-DDTHH:MM"
  last_turn: "YYYY-MM-DDTHH:MM"
  turn_count: 0
  summary: "{rolling one-line summary}"

events_logged:
  - turn: 1
    type: decision | experiment | dead_end | pivot | observation | ...
    id: "{N/O}{XX}"
    routing: direct | staged | crystallized
    provenance: user | ai-suggested | ai-executed | user-revised
    summary: "{telegraphic what}"

ai_actions:
  - turn: 1
    action: "{what AI did}"
    provenance: ai-executed
    files_changed: ["{paths}"]

claims_touched:
  - id: C{XX}
    action: created | crystallized | advanced | weakened | confirmed | refuted | withdrawn | revised | split | merged
    turn: 1

logic_revisions:                  # full before/after for every edit Stage 4 makes
  - turn: 1
    entry: C{XX}                  # or H{XX}, concept id, etc.
    field: Statement | Status | Rationale | Dependencies | id | ...
    before: "{prior value, verbatim}"
    after: "{new value, verbatim}"
    signal: empirical-resolution | verbal-declaration | dependency-change | artifact-commitment | terminology-drift | user-directive
    provenance: user | ai-suggested | user-revised
    note: "{one-line why, optional}"
  # structural changes record both endpoints, e.g. for a split:
  - turn: 1
    entry: C07
    field: split
    before: "C07 covered both training and inference"
    after: "C07 = training-time claim; C12 = inference-time claim"
    signal: verbal-declaration
    provenance: user-revised

key_context:
  - turn: 1
    excerpt: "{quote or paraphrase capturing decisive exchange}"

open_threads:
  - "{what needs follow-up}"

ai_suggestions_pending:
  - "{unconfirmed AI suggestions still awaiting closure}"
```

### Session Index (`trace/sessions/session_index.yaml`)

```yaml
sessions:
  - id: "YYYY-MM-DD_NNN"
    date: "YYYY-MM-DD"
    summary: "{main outcome}"
    turn_count: {N}
    events_count: {N}
    claims_touched: [C{XX}, ...]
    open_threads: {N}
```

### Reasoning Log (`trace/pm_reasoning_log.yaml`) — self-continuity

A few lines per turn explaining the manager's own organizational decisions. Cheap on
tokens, prevents organizational drift.

```yaml
entries:
  - turn: "YYYY-MM-DD_NNN#3"
    notes:
      - "Staged O07 as potential_type: heuristic (not claim) — it's a how, not a what."
      - "Did NOT crystallize O05 despite affirmation-like language: user said 'maybe' not 'yes'."
      - "Routed N12 as dead_end rather than experiment — code was abandoned mid-run."
```

## Initialization (if `ara/` does not exist)

Create the structure on the first turn that contains research-significant activity. Do not
ask unprompted on a purely conversational opener.

```
mkdir -p ara/{logic/solution,src,trace/sessions,evidence/{tables,figures},staging}
```

Seed:
1. `ara/PAPER.md` — root manifest (infer title, authors, venue from project context)
2. `ara/trace/sessions/session_index.yaml` — `sessions: []`
3. `ara/trace/exploration_tree.yaml` — `tree: []`
4. `ara/trace/pm_reasoning_log.yaml` — `entries: []`
5. `ara/staging/observations.yaml` — `observations: []`
6. `ara/logic/claims.md` — `# Claims`
7. `ara/logic/problem.md` — `# Problem`
8. `ara/logic/solution/heuristics.md` — `# Heuristics`
9. `ara/evidence/README.md` — `# Evidence Index`

Then run the per-turn procedure normally.

## Briefing (fresh conversation only)

On the first turn of a new conversation (not every turn), silently read:
- latest session record's `summary`, `open_threads`, `ai_suggestions_pending`, `key_context`
- `claims.md` status counts
- `staging/observations.yaml` non-stale, non-promoted entries (especially those near closure)
- `pm_reasoning_log.yaml` last few entries (organizational continuity)

Surface relevant pieces only when they bear on the user's first task — never lead with a
formal briefing the researcher did not ask for. If the user asks "where did we leave off",
deliver the full briefing.

## Rules

1. **End-of-turn only; never mid-turn.** Skip empty turns (greetings, ack, formatting).
2. **Never fabricate.** Log only what actually happened or was discussed.
3. **Stage interpretive events by default; crystallize only on a closure signal** — abandonment / affirmation / resolution / commitment. No counters, no LM-judged maturity.
4. **Never auto-upgrade provenance.** `ai-suggested` holds until explicit user affirmation.
5. **Stage 4 defaults to no change.** Edits require an explicit signal this turn; terminal states (`refuted`/`withdrawn`) need explicit triggers, never silence/staleness. Log near-misses.
6. **Respect layer mutability** (see top): `logic/` overwrites in place; `trace/` and `staging/` are append-only except forward-reference pointers. Every logic edit gets a `logic_revisions:` before/after in the session record — the only place pre-edit content is kept.
7. **Never silently overwrite contradictions** — flag both, append an `unresolved` decision node, defer.
8. **Read target files first** (correct IDs, no dupes); establish forensic bindings (claim→proof, heuristic→code, decision→evidence), `[pending]`+TODO if not yet bindable. Keep YAML valid; summary line terse.
