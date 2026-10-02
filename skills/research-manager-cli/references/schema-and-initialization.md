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
## C{XX}: {generalized title — the takeaway, not a recipe name}
- **Statement**: {the generalized, mechanistic conclusion; subject = a mechanism/relationship, never a named recipe; carries NO run numbers}
- **Conditions**: {under what conditions it holds; the regime; the known untested boundary}
- **Sources**: [{one entry per load-bearing number in the claim (now in `Conditions`/`Proof`): `<value> ← <file:line | trace-node:field> «verbatim line copied from source» [input|result]`, or `<value> ← [pending: reason]`}]   # see "Number grounding"; a bare path with no «quote» is invalid
- **Status**: hypothesis | untested | testing | supported | weakened | refuted | withdrawn
- **Provenance**: user | ai-suggested | user-revised
- **Falsification**: {a concrete observation that would disprove it — for a mechanism claim, about the system/world; for a methodological/regime claim, about the benchmark's behavior. NOT a tautology or a re-run of the same gate ("if the recipe fails the gate")}
- **Proof**: [{evidence refs (→ evidence/) or "pending"; run numbers/IDs/scores live HERE, not in Statement}]
- **Dependencies**: [C{YY}, ...]
- **Tags**: {comma-separated}
- **Last revised**: YYYY-MM-DD (turn-id)   # pointer back to the trace; absent until first revision
- **Taste** (optional):   # researcher's own reactions; see references/taste-comments.md — absent until the first one
  - [YYYY-MM-DD] `endorse | uncertain | reject` on `claim | evidence | framing | priority` — {free-text comment}
```

**The Statement is the generalized conclusion the evidence supports — a mechanism or relationship,
not a restatement of run numbers.** What keeps it falsifiable and honest is `Conditions` (the regime
it holds in + the untested boundary) plus a `Falsification`, not a narrowed sentence. Numbers (run
IDs, n, scores, step counts) belong in `Proof` → `evidence/` (grounded per Number grounding), never
in `Statement`. `Conditions` is mandatory: a generalized Statement with no Conditions is an unbounded
slogan.

**Calibrate the Statement to what the evidence actually separates.** Do not assert a distinction the
design cannot disentangle (confounded factors — e.g. matrix "shape" vs "role" when they co-vary), or
a law from a single instance. When that's the case, hedge in the Statement itself — name the
unseparated factors together, or say "shown once here" — rather than only burying it in `Conditions`.
`Conditions` bounds *where* the claim applies; it is not a license for the Statement's verb to
over-reach. The Statement/Conditions may be sharpened on a later turn (Stage 4 content revision) as
the mechanism becomes clearer — no new closure signal is needed.

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

