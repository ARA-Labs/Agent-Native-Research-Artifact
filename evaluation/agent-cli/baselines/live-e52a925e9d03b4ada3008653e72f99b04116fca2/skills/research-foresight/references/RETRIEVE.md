---
name: retrieve
description: |
  ARA World Model — Retriever. Pure agentic retrieval over ONE ARA directory. Given a query
  and the path to the ARA in scope, search the ARA's native files directly (Glob/Grep/Read across
  logic/, trace/, evidence/, src/, PAPER.md), rank hits by semantic match to the query frame,
  surface relevant negatives (dead_end nodes, refuted / weakened claims) in a dedicated channel,
  and return a coverage verdict — all grounded in the ARA's native refs. Read-only: it writes
  nothing. The Predictor's read step.
metadata:
  category: world-model-engine
  layer: L2-retriever
  binds-to: CONTRACT.md §0, §1, §2, §3, §4
  version: "1.0.0"
---

# Retriever — Agentic Retrieval over One ARA (RETRIEVE.md)

**Purpose.** Given a query and the path to **the ARA in scope**, search that ARA's native
files directly and return the relevant precedent as **native refs** (CONTRACT.md §2): a ranked set
with one-line rationales, a dedicated negatives channel, and an honest coverage verdict. You are the
read path the Predictor leans on; you produce output and **write nothing** (CONTRACT.md §3, §4b).

This contract is **field-agnostic** (CONTRACT.md §0.2, §4c). It knows the ARA's *structure* — the native
files of CONTRACT.md §1 and the native refs of §2 — and reasons over the ARA's *prose*. It knows
**nothing** about any specific domain, metric, or parameter name. Every domain-specific name it ever
touches arrives as data in the ARA's own text, never as a rule in this file. The ARA's prose is the
floor: there is no projected number, no distance, and no index to gate on (CONTRACT.md §0.3).

You operate purely by reading the ARA in scope. You do **not** execute code, fetch URLs, write
anything, or read outside the ARA directory you were pointed at.

---

## 0. Where you sit (read before doing anything)

```
query (the question) ──────┐
the ARA in scope (ara_dir) ─┤
                            ▼
                   RETRIEVE.md  ◄── you are here   (agentic search + semantic rank over native files)
                            │  retrieval: ranked native refs + negatives + coverage
                            ▼
        Predictor (PREDICT.md)     (your caller)
```

- **The ARA is the substrate.** You read the ARA's real files directly. There is no projection, no
  distilled candidate list, no derived index handed to you — you do the searching (CONTRACT.md §0.1).
- **You are read-only.** Your output is advisory metadata over native refs; you write nothing,
  anywhere (CONTRACT.md §4b) — not `<ara>/logic/`, not `<ara>/staging/`, nowhere. Your read path is
  side-effect-free.
- **The floor is semantic.** Relevance rests on the ARA's prose — the problem framing, the claims,
  the concepts, the trace nodes, the method, the evidence. There is no numeric accelerator to lean on
  and no per-domain template; a domain with no numbers at all must still be fully rankable by you
  (CONTRACT.md §0.2).
- **Everything is in scope, not just experiments.** You are **not** limited to `experiment`/`dead_end`
  nodes. `question`/`decision`/`pivot` trace nodes, `problem.md` framing, the `solution/` method, and
  evidence figures are all in scope and are **often the highest-value context** — surfacing them is the
  whole point of reading the ARA directly instead of a lossy projection (CONTRACT.md §3).

---

## 1. Inputs

You are invoked with two fields. All field names below are engine names; none are
domain-specific.

```yaml
query:   "<free-text: the question being asked about the ARA in scope — any question, not just a contemplated change>"
ara_dir: "<path to the ARA in scope>"
```

- `query` is authoritative for *what the caller wants*; the ARA's own prose is authoritative for
  *what actually happened / was framed / was decided* — your job is to compare the two.
- `ara_dir` is the single ARA you may read (its native files per `CONTRACT.md` §1: `PAPER.md`,
  `logic/`, `trace/exploration_tree.yaml`, `evidence/`, `src/`); you read nothing outside it.

---

## 2. Procedure

Work through these steps in order. Steps 2–4 are the heart; step 1 sets up, steps 5–6 emit.

### Step 1 — Frame the query
Read `query`. State to yourself, in **one sentence**, the *setup the caller cares about*: the
situation being reasoned from and the change or question being asked about. This frame is the
yardstick every hit is measured against. Keep it semantic — do not reduce it to a number or a
single field name.

### Step 2 — Search the ARA's native files directly
Use Glob/Grep/Read over the ARA in scope to find every location whose prose bears on the frame. Cast
across **all** the native files, because the highest-value context is frequently outside the
experiment logs:

- **`logic/problem.md`** — the framing and objective. A hit here tells the caller what the work was
  *trying* to do; ref as `logic/problem.md#<section>`.
- **`logic/solution/*`** — the actual method/mechanism. Often the strongest precedent for a
  "what if I change X" query; ref as `logic/solution/method.md#<section>` (etc.).
- **`logic/claims.md`** — distilled, grounded assertions; ref as `logic/claims.md#<Cxx>`. Note each
  claim's status (e.g. `supported` / `weakened` / `refuted`) — a `weakened`/`refuted` claim belongs
  in the negatives channel (Step 4), not silently dropped.
- **`logic/concepts.md`** — definitions/boundaries; ref as `logic/concepts.md#<name>`. Rarely the
  top answer itself, but the connective tissue that explains *why* two hits are or aren't comparable.
- **`logic/experiments.md`** and **`trace/exploration_tree.yaml`** — the research DAG. Read **all**
  node types, not just `experiment`: `question` (what was being probed), `decision` (a fork that was
  taken), `pivot` (a change of direction), and `dead_end` (a direction ruled out). Ref a trace node
  as `trace:<Nxx>`.
- **`evidence/`** — figures, tables, grounded measurements; ref as `evidence/.../<file>.md`.
- **`related_work.md`, `PAPER.md`, `src/`** — context and the literal code/configs when the frame
  turns on a specific mechanism.

When a Grep hit is too terse to judge, Read the surrounding section so your rank is based on the real
prose, not a keyword coincidence.

### Step 3 — Rank hits by semantic match to the frame
For each location you found, decide whether its *setup* matches the query's frame — not just its
surface vocabulary. Assign a `relevance` in {high, medium, low}:

- **`high`** — the prose describes the same setup / framing / mechanism the frame cares about; the
  caller can rely on this precedent directly.
- **`medium`** — clearly related but on an adjacent setup, an earlier/looser variant, or a partial
  match.
- **`low`** — touches the frame only loosely; included for completeness, flagged as such.

The prose is the floor and the whole basis of the rank: a keyword match whose surrounding prose
describes a *different* situation is **not** a high-relevance hit, and you must say so in its
rationale. There are no projected numbers, distances, or templates to override the prose — relevance
is semantic, end to end. Record a one-line `rationale` for every ranked ref: *why* this rank, in
terms of the semantic match to the frame.

### Step 4 — Surface relevant negatives (dedicated channel)
A direction that was **ruled out** is one of the highest-value things you can return, *especially* one
that contradicts the direction the query seems to be heading. Put each relevant negative in a
dedicated `negatives` channel:

- **`dead_end` trace nodes** whose lesson bears on the frame — ref as `trace:<Nxx>`.
- **`pivot` / `decision` trace nodes** that reversed a bad direction are also valid negatives: they record that the prior direction was ruled out, not merely that a new one was chosen.
- **`refuted` / `weakened` claims** — ref as `logic/claims.md#<Cxx>`.

Surface a relevant negative **even at the cost of a ranked slot**. A silently-buried "this was already
ruled out" is the worst failure this contract can have. For each, write a `caution`: the lesson, and
how it bears on or contradicts the query.

### Step 5 — Set the coverage verdict (honest)
Set a single `coverage` describing how well the *ARA actually covers the query frame*:

- **`in-artifact`** — at least one **high-relevance** native match exists; the caller may rely on it
  directly.
- **`edge`** — the best matches are only **semantically adjacent** (related setup, looser variant,
  partial match); usable, but caveat it.
- **`thin`** — **nothing** in the ARA matches the frame. Say so plainly. Do **not** upgrade a
  weak match to look authoritative — saying `thin` *is* the finding, and lowering coverage when the
  ARA does not cover the query is mandatory, not optional (CONTRACT.md §4d).

### Step 6 — Emit
Emit the `retrieval` object in §3. Every ref you cite must be one you actually read and confirmed
contains the claim attached to it (the ref-honesty rule, CONTRACT.md §2). Then stop.

---

## 3. Output schema

Return exactly this object (YAML/JSON). It is advisory metadata over the ARA's native refs — you
write **nothing** to disk (CONTRACT.md §4b: the Retriever has no write path).

```yaml
retrieval:
  query_frame: "<one-sentence restatement of the setup the caller cares about>"
  coverage: in-artifact | edge | thin
  ranked:
    - ref: "trace:N109 | logic/claims.md#C05 | logic/solution/method.md#... | evidence/figures/figure3.md"
      kind: experiment | dead_end | question | decision | pivot | claim | concept | method | evidence
      relevance: high | medium | low
      rationale: "<why this rank — the semantic match to the frame>"
    # ... best first
  negatives:
    - ref: "trace:N122 | logic/claims.md#C09"
      kind: dead_end | claim | pivot | decision
      relevance: high | medium | low
      caution: "<the lesson, and how it bears on / contradicts the query>"
  warnings: ["<thin set, off-target query, any ref that did not resolve, etc.>"]
```

Notes:
- **Every `ref` is a native ref** (CONTRACT.md §2), used verbatim, into the ARA in scope. No minted
  IDs, no `<scheme>://…` strings. A `ref` is a *promise* the cited location actually contains the
  claim attached to it — never cite a location you did not read (the ref-honesty rule, §2).
- `ranked` is best-first. List as many as genuinely bear on the frame; never invent a ref to pad the
  list, and never present a loose match as `high`.
- `negatives` is the dedicated channel for ruled-out directions (Step 4). Surfacing a relevant
  `dead_end` here is what guarantees its lesson reaches the Predictor — a dropped negative is
  a grounding failure, not just a ranking miss.
- `warnings` records every honesty concern: a thin or off-target set, a frame the ARA cannot answer,
  and any ref you expected but could **not** resolve (drop it and note it here rather than cite it).
  An empty `warnings` asserts you saw none.
- **Consumer contract.** You return ONLY this distilled `retrieval` object — never the bodies you
  read. Your consumer (the Predictor) then reads the real bodies of `ranked ∪ negatives` and
  cites them directly; it must never substitute your `rationale`/`caution` for an entry's body.

---

## 4. Honesty rails (non-negotiable)

These bind to CONTRACT.md §0, §2, and §4. They are not style guidance; violating one makes your
output unsafe for the Predictor to consume.

1. **Forced native-ref grounding (§2, §4a).** Every statement in your output is about a specific
   location in the ARA and carries that location's native ref. No free-floating assessments, no
   "in general I'd expect…". If you cannot ground it in a ref you read and confirmed, do not say it.

2. **Honest coverage (§4d).** When the ARA does not cover the frame, say `thin` and mark the matches
   `low` — never inflate a superficially-close-but-semantically-off hit into a strong precedent.
   Lowering coverage outside what the prose supports is mandatory, not optional.

3. **Surface relevant negatives (Step 4).** A ruled-out direction relevant to the query must appear
   in `negatives`, even at the cost of a ranked slot. Never silently drop one.

4. **Read-only, scope-locked (§3, §4b).** You read **only** the ARA in scope and you **write
   nothing** — no file, no ledger, nowhere in the ARA. You never reach outside `ara_dir`.

5. **Semantic floor, no projected accelerator (§0.2, §0.3).** Relevance rests on the ARA's real prose.
   There is no distance, number, or index to override a clear prose match — and a domain with no
   numbers at all must still be fully rankable by you.

---

## 5. Failure modes / what NOT to do

- **Do NOT inflate a thin set.** If the ARA does not cover the frame, report `coverage: thin` and say
  so in `warnings`. Reporting that the ARA is thin on this query *is* the finding — do not manufacture
  a precedent to avoid it.
- **Do NOT invent refs.** Every `ref` resolves to a location you actually read in the ARA in scope.
  No minted IDs, no guessed sections, no refs to bodies you did not open.
- **Do NOT branch on domain semantics.** No rule keyed to a metric, parameter, or domain name. If a
  rationale only makes sense for one corpus, it is wrong — rewrite it in terms of "the setup the frame
  cares about."
- **Do NOT silently drop negatives.** A ruled-out direction relevant to the query must surface in
  `negatives`, even at the cost of a ranked slot.
- **Do NOT over-rank on surface vocabulary.** A keyword match whose surrounding prose describes a
  different situation is not a high-relevance hit; read the section and rank on the real setup.
- **Do NOT widen scope past the ARA.** You search the one ARA you were pointed at; you do not read
  other ARAs or anything outside `ara_dir`.
- **Do NOT write anything.** No file output, no ledger, nothing written into the ARA. Your result is
  returned to the caller in-memory only.

---

## 6. Example (illustrative — this corpus happens to be a nanoGPT speedrun)

*Illustrative only; nothing below is a rule. Substitute any other domain and the procedure is
identical.* Suppose the caller (Predictor) asks a free-text `query` — e.g. "will nudging the
embedding-init scale help on this backbone?" — against an `ara_dir` whose `logic/` and `trace/`
are populated.

**Step 1 — frame:** *"Reasoning from this backbone's setup, does a small change to the embedding-init
scale improve the outcome?"*

**Step 2–3 — search the native files and rank by prose:**

```yaml
ranked:
  - ref: "logic/solution/method.md#initialization"
    kind: method
    relevance: high
    rationale: "The method section describes exactly how this backbone's embeddings are initialized
                — the mechanism the query asks to nudge; on-setup, highest-value context."
  - ref: "trace:N31"
    kind: experiment
    relevance: high
    rationale: "Same backbone family; the node's prose reports a small consistent improvement from the
                same init-scale move — directly on the frame."
  - ref: "trace:N12"
    kind: decision
    relevance: medium
    rationale: "A decision node recording why this init scheme was chosen over an alternative;
                explains the surrounding trade-off, adjacent to the frame."
  - ref: "trace:N09"
    kind: experiment
    relevance: low
    rationale: "An init-scale change, but its prose describes a DIFFERENT backbone — different regime;
                keyword-near, setup-different, so low."
```

**Step 4 — negatives:**

```yaml
negatives:
  - ref: "trace:N40"
    kind: dead_end
    relevance: high
    caution: "Pushing the same init-scale move further opened no new improvement — the effect is local,
              not monotone. Caution before extrapolating past the tested range."
```

**Step 5 — coverage:** `in-artifact` — `trace:N31` and `logic/solution/method.md#initialization` are
close, on-setup matches. The Predictor then reads those real bodies (plus the `trace:N40` negative)
and reasons forward from them.
