# Live PM — Schemas and Initialization

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

Load local `references/property-authoring.md` directly and unconditionally before
claim capture, staging, semantic revision, or executable authoring. The existing
fields below preserve source assertions and obligation versions; no new core ARA
schema is required. The shared contract governs evidence meaning, executable specs,
check identities, and isolated ARA-only extraction without relaxing CLI-only access
or the manager's closure signals.

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
    taste_log.yaml                  #   OPTIONAL — researcher's taste comments on trace nodes (pointer-only, never edits the node)
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

The tree's shape stays recoverable from a flat append log through two fields you already write: mark
each level/phase **boundary** as a `pivot` (or `question`) node (it opens a new branch), and list what
a node builds on in `also_depends_on`. Only when a node resumes an **earlier** branch — rather than
continuing the step right before it — add an explicit `parent: N{XX}` to point back; in the common
case its place is already implied and no extra field is needed.

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
    also_depends_on: []  # cross-edges (ids) — what this node builds on
    parent: N{XX}        # OPTIONAL — only to point back to an earlier branch; omit when implied
    children:
      - { ... }
```

### Claim (`logic/claims.md`) — crystallized only

```markdown
## C{XX}: {title identifying the bounded assertion or separately authored synthesis}
- **Statement**: {verbatim source assertion, including named methods, quantitative commitments, and every conjunct; a separately identified synthesis may instead state a bounded interpretation}
- **Conditions**: {exact method variant/baseline, metric, units, task scope, quantifier, aggregation, uncertainty, unresolved meaning, and known untested boundaries}
- **Sources**: [{source revision/anchor and assertion identity; one entry per load-bearing number anywhere in the claim: `<value> ← <file:line | trace-node:field> «verbatim line copied from source» [input|result]`, or `<value> ← [pending: reason]`}]   # see "Number grounding"; a bare path with no «quote» is invalid
- **Status**: hypothesis | untested | testing | supported | weakened | refuted | withdrawn
- **Provenance**: user | ai-suggested | user-revised
- **Falsification**: {a concrete observation that would disprove this exact assertion, including its metric, scope, variant, and conjuncts; not a tautology}
- **Proof**: [{evidence refs (→ evidence/) or "pending"; preserve raw headers, axes, method identities, uncertainty, and provenance in linked evidence}]
- **Dependencies**: [C{YY}, ...]
- **Tags**: {comma-separated}
- **Last revised**: YYYY-MM-DD (turn-id)   # pointer back to the trace; absent until first revision
- **Taste** (optional):   # researcher's own reactions; see references/taste-comments.md — absent until the first one
  - [YYYY-MM-DD] `endorse | uncertain | reject` on `claim | evidence | framing | priority` — {free-text comment}
```

**A Statement may be a bounded empirical comparison, hypothesis, or mechanism claim.**
Named configurations, values, and statistical commitments belong in the Statement
when they are part of the source assertion. Preserve the verbatim assertion and its
source identity; `Conditions` makes its scope explicit and never licenses changing it.
Ground load-bearing numbers per Number grounding in SKILL.md. Do not insert new
evidence numbers into a preserved quotation or copy them into executable operands.

**Separate reporting from interpretation.** A source assertion is recorded faithfully
even when unsupported, contradicted, or confounded. Mark those limitations in
`Conditions`/`Proof` and status under the existing signals. A synthesized explanation
must be a separate claim linked to the preserved assertions; calibrate that synthesis
to what the evidence separates, rather than asserting a law from a single instance.
Later revisions follow Stage 4 signals and retain immutable full before/after versions.

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
- **Taste** (optional):   # researcher's own reactions; see references/taste-comments.md — absent until the first one
  - [YYYY-MM-DD] `endorse | uncertain | reject` on `claim | evidence | framing | priority` — {free-text comment}
```

Current-state snapshot only (same as claims); history lives in the trace.

### Observation (`staging/observations.yaml`) — staged

```yaml
observations:
  - id: O{XX}
    timestamp: "YYYY-MM-DDTHH:MM"
    provenance: user | ai-suggested | ai-executed | user-revised
    content: "{verbatim selected assertion with all conjuncts; otherwise raw observation}"
    context: "{source revision/anchor, immutable version/digest, full meaning/scope, evidence refs and before/after-evidence timing, unknowns and linked authoring/unsupported-reason records}"
    potential_type: claim | heuristic | concept | constraint | architecture | unknown
    bound_to: [N{XX}, ...]    # exploration nodes this depends on
    promoted: false
    promoted_to: null         # e.g., "logic/claims.md:C07" once crystallized
    crystallized_via: null    # which closure signal fired
    stale: false
```

Stage selected assertions through `observation.stage` at the first epilogue opportunity,
before evidence when possible. Record when evidence already existed; same-turn or
retrospective recording is not preregistration. This append-only buffer is also the
obligation ledger before crystallization. Missing evidence or no supported relation
retains the full obligation and its specific reason in linked session/authoring records.
It remains staged unless an existing closure signal fires; execution capability
neither grants nor vetoes crystallization. Retain its source assertion ID in the
all-selected-assertions denominator; generated subclaims do not enlarge it.

Recording, spec creation, and a holding reported-evidence check alone do not satisfy a
closure signal or affirm truth. Keep prospective candidates staged until an actual
existing signal fires. Append semantic revisions as new linked observations rather
than editing old `content`/`context`. Before changing meaning or decision policy, retain
full immutable before/after obligation and candidate versions in `logic_revisions:`
and linked authoring receipts. Preserve source revisions, digests, and split/merge
correspondence. Historical checks apply only to the exact versions they checked; a new
version needs its own separately authorized check and replay or an explicit unchecked
reason. Use the shared contract for complete evidence/spec/check semantics and the
allowlisted input view required for isolated ARA-only extraction.

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

logic_revisions:                  # full before/after for every edit and obligation/candidate version change
  - turn: 1
    entry: C{XX}                  # or O{XX}, linked candidate, H{XX}, concept id, etc.
    field: Statement | Conditions | Status | Rationale | Dependencies | content | context | id | ...
    before: "{prior value verbatim; full immutable obligation/candidate content for semantic revisions}"
    after: "{new value verbatim; full immutable obligation/candidate content for semantic revisions}"
    signal: empirical-resolution | verbal-declaration | dependency-change | artifact-commitment | terminology-drift | user-directive
    provenance: user | ai-suggested | user-revised
    note: "{why; source revision, before/after digests, version correspondence and linked authoring/check receipt when applicable}"
  # structural changes retain complete endpoints, not just a summary:
  - turn: 1
    entry: C07
    field: split
    before: "{complete verbatim C07 entry before split, including both obligations}"
    after: "{complete C07 and C12 entries after split, with correspondence to the retained source obligation}"
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

### Taste Log (`trace/taste_log.yaml`) — optional, append-only

Researcher's taste comments on trace nodes. Never edits `exploration_tree.yaml` — points at
it instead, the same way a promoted observation points at its logic-layer destination
without rewriting itself. See `references/taste-comments.md` for trigger detection, target
resolution, and the confirm-before-write procedure. File does not exist until the first entry.

```yaml
entries:
  - id: T{XX}
    timestamp: "YYYY-MM-DDTHH:MM"
    target: N{XX}                         # trace node this comments on; never edited
    tag: endorse | uncertain | reject
    object: claim | evidence | framing | priority
    comment: "{free-text comment}"
```

## Initialization (if `ara/` does not exist)

Create the structure on the first turn that contains research-significant activity. Do not
ask unprompted on a purely conversational opener.

Submit an external JSONL request through `ara -C ara apply <request.jsonl> --json` with
`{"op":"artifact.init","profile":"research-manager","paper":"<complete inferred root manifest>","missing_only":true}`.
The bounded operation creates the same source structure and seed set below, preserving
existing default-seed contents; explicitly supplied existing bytes must match exactly.
For an existing root read PAPER through ara first and supply its exact complete bytes,
not a regenerated manifest. Conflicting supplied seeds reject without mutation.

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

