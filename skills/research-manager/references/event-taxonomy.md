# Event Taxonomy & Routing Rules

Canonical reference for **Stage 2 (Event Router)** of the Live PM pipeline. Loaded on
demand at epilogue time. SKILL.md owns the pipeline orchestration, closure signals,
crystallization procedure, contradiction trigger, and schemas — this file does not
duplicate those.

This document covers two axes:

| Axis | Question | Outcome |
|------|----------|---------|
| **Kind** | What kind of event is this? | Picks the schema and target layer. |
| **Routing** | Is this a journey fact or interpretation? | Picks **direct** vs **staged**. |

A journey fact records *what occurred* (a choice, a run, an abandonment). It is immutable
and goes direct. An interpretive claim records *what something means or what is generally
true*. It is revisable, goes staged, and only crystallizes on a closure signal.

## Direct-Routed Events (Journey Layer)

Write to `trace/exploration_tree.yaml` immediately at end of turn.

| Type | Signals | Required payload |
|------|---------|------------------|
| `question` | "What if...", "Should we...", "How does...", a research direction opened | `description` |
| `decision` | User chose between alternatives, committed to a direction | `choice`, `alternatives`, `evidence` |
| `experiment` | Code ran a test/benchmark, results produced | `result`, `evidence` |
| `dead_end` | Approach abandoned, hypothesis falsified, "doesn't work", reverted | `hypothesis`, `failure_mode`, `lesson` |
| `pivot` | Major direction change triggered by evidence | `from`, `to`, `trigger` |

A `decision` node MAY reference a staged observation as evidence — this counts as
**artifact-commitment** for that observation (closure signal; see SKILL.md Stage 3).

`ai-action` events (AI wrote code, ran a command) go to the session record's `ai_actions`
list, **not** to the exploration tree.

## Staged-Routed Events (Interpretive — Buffered for Maturity)

Write to `staging/observations.yaml` first, with `potential_type` indicating where they
would crystallize. They do **not** enter `logic/` until a closure signal fires (see
SKILL.md Stage 3).

| Candidate Event | Signals | Crystallizes To | `potential_type` |
|-----------------|---------|-----------------|------------------|
| `claim` | "I believe...", "The system achieves...", falsifiable assertion about capability/property | `logic/claims.md` | `claim` |
| `heuristic` | "The trick is...", "You need to...", implementation rule with rationale | `logic/solution/heuristics.md` | `heuristic` |
| `concept` | New term defined, disambiguation needed | `logic/concepts.md` | `concept` |
| `constraint` | "This only works when...", boundary condition | `logic/solution/constraints.md` | `constraint` |
| `architecture` | System design statement, component relationship | `logic/solution/architecture.md` | `architecture` |
| (unclassified) | Interesting but not yet typed | (stays staged) | `unknown` |

Evidence artifacts (tables, figures, metrics) referenced by a direct-routed `experiment`
get written to `evidence/` immediately — they are raw data, not interpretation.

## Routing Decision Tree

```
What KIND of event is this?

  Journey fact (something that happened)?
    Was a choice made between alternatives?
      → decision  [DIRECT to trace/]
    Did code/test produce a result?
      → experiment  [DIRECT to trace/, plus evidence/ for artifacts]
    Was an approach abandoned with a reason?
      → dead_end  [DIRECT to trace/]
    Was there a major direction change?
      → pivot  [DIRECT to trace/]
    Was a research question opened?
      → question  [DIRECT to trace/]
    Did the AI perform an action (write code, run command)?
      → ai-action  [session record only]

  Interpretation (something asserted to be true / general)?
    Generalizable falsifiable assertion (a mechanism/relationship, bounded by conditions)?
      → STAGE as potential_type: claim
    Implementation rule with rationale?
      → STAGE as potential_type: heuristic
    Term definition?
      → STAGE as potential_type: concept
    Boundary condition?
      → STAGE as potential_type: constraint
    System-design statement?
      → STAGE as potential_type: architecture
    Doesn't fit?
      → STAGE as potential_type: unknown
```

## Skip Filter (no record)

Do not write any record for these:
- Routine file reads with no downstream decision
- Typo fixes, formatting changes, lint passes
- Git status checks, dependency installs, environment setup
- Greetings, acknowledgments, "thanks"
- Clarifying questions whose answer added no new content
- Pure restatement of the user's request

If a turn contains only skip-filter activity, print
`[PM] Turn skipped: no research events.` (or stay silent) and exit the epilogue.

## Provenance Assignment

```
Who generated this information?

User said it directly (typed it, stated it, confirmed it)
  → provenance: user

AI inferred it from code, output, or conversation context
  → provenance: ai-suggested

AI performed an action (wrote code, ran test, made edit)
  → provenance: ai-executed

User modified an AI suggestion ("no, actually..." / "more like...")
  → provenance: user-revised

Uncertain?
  → provenance: ai-suggested  (conservative default)
```

`ai-suggested` never auto-upgrades. A subsequent **verbal-affirmation** closure signal
upgrades it to `user-revised` (or `user` if the affirmation reproduces the assertion
verbatim). The other three closure signals license crystallization but do **not** change
provenance.

### Trust calibration

The provenance distribution of an artifact is itself a quality signal: a project full of
`ai-suggested` claims is less trustworthy than one full of `user` / `user-revised` claims.
Reviewers and downstream tools (e.g., rigor-reviewer L2) inspect this distribution.

## ID Conventions

| Type | Prefix | Example | Scope |
|------|--------|---------|-------|
| Exploration node | N | N01, N02 | Global (across all turns and sessions) |
| Claim | C | C01, C02 | Global; assigned at crystallization, not at staging |
| Heuristic | H | H01, H02 | Global; assigned at crystallization |
| Experiment plan | E | E01, E02 | Global |
| Observation | O | O01, O02 | Global; assigned at staging |
| Session | date_seq | 2026-04-27_001 | Unique per calendar day |

Always read the target file to find the highest existing ID before assigning a new one.

## Forensic Binding Checklist

Establish at write time. If a binding is not yet possible, write `[pending]` and leave a
TODO comment so a future epilogue can complete it.

- **Claim → Proof**: at crystallization, what evidence supports/refutes it?
- **Experiment → Claim**: which staged or crystallized claim does this experiment test?
  This binding is what enables the **empirical-resolution** closure signal.
- **Heuristic → Code**: where in the codebase is this implemented?
- **Decision → Evidence**: which exploration nodes or evidence artifacts motivated it?
- **Dead End → Lesson**: what was learned that prevents repeating the mistake?
- **Observation → Bound nodes**: at staging time, list `bound_to: [N{XX}, ...]` for any
  exploration nodes the observation depends on. Without this list, empirical-resolution
  cannot be detected automatically.
