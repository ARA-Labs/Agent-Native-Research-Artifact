# ARA World Model — Engine Contract (the shared interface)

> This file is the **single source of truth** the engine binds to. The two agent contracts
> (`RETRIEVE.md`, `PREDICT.md`) conform to the grounding references, read-only isolation, and
> invariants defined here. If two documents disagree, **this file wins**.
>
> Scope = **single-ARA** operation: the engine reads **one ARA directory** directly. Multi-ARA
> federation is a later layer; the references below are chosen so it can be added **without
> renaming anything** (see §2).

---

## 0. First principles

1. **The ARA is the substrate.** The engine reads an ARA's native files **directly** — there is
   no projection step, no intermediate distilled database, and no global-ID scheme. The ARA produced by the compiler
   (`PAPER.md`, `logic/`, `trace/`, `evidence/`, `src/`) is already a structured, machine-readable
   artifact; the World Model reasons over *that*, not over a lossy copy of it. Grounding is the
   ARA's own native anchors (§2), used verbatim.

2. **Field-agnostic.** The engine knows the ARA's *structure*, never its domain. Which quantity is
   the objective, whether more is better, and what any domain term means arrive as **data in the
   ARA's own text** (the `problem.md` objective, the method, the evidence) — never from a rule in
   the engine, and never from your own priors about the field. The same engine works on a biology
   ARA, an HCI ARA, anything.

3. **Agentic core.** The two contracts (`RETRIEVE.md`, `PREDICT.md`) are **agentic**: each reads
   the ARA's prose and reasons over it. There is **no deterministic projection, distance, or index
   layer**; relevance and inference are semantic, over the ARA's real prose.

4. **Native-ref grounding.** Every assertion a contract makes carries one or more **native refs**
   into the ARA (§2) — used verbatim, with **no minted IDs**: trace node `trace:N109`; claim
   `logic/claims.md#C05`; concept `logic/concepts.md#<name>`; method/problem `<file path>#<section>`;
   evidence `evidence/.../<file>.md`. A ref promises the cited location actually contains the claim.

5. **Grounded answering over the ARA.** The Predictor reads the ARA and **answers any question
   grounded in it** — forward prediction (reasoning forward from the mechanism to a novel, falsifiable
   hypothesis about a contemplated change) is the **marquee case, not the only one**; it separates
   `grounded_inference` from a named `speculative_leap` and commits to a checkable point. The engine
   is **read-only** (§4b).

---

## 1. Engine layout

```
research-world-model/                # ENGINE — the skill, all-English contracts, no per-ARA data
  SKILL.md                           # entry point: retrieve precedent, then answer the question
  references/
    CONTRACT.md                      # this file — the foundation both contracts bind to
    RETRIEVE.md                      # agentic retrieval over ONE ARA's native files
    PREDICT.md                       # grounded answerer over one ARA (forward prediction = marquee case)

<ara_dir>/                           # THE SUBSTRATE — read directly, never copied or projected
  PAPER.md                           # the narrative
  logic/                             # claims.md, concepts.md, problem.md, experiments.md,
                                     #   related_work.md, and solution/* (the actual method layer)
  trace/                             # exploration_tree.yaml — the FULL DAG:
                                     #   experiment, dead_end, question, decision, pivot
  evidence/                          # figures/, tables/, ... — grounded evidence
  src/                               # code / configs / data as the work warrants
```

The engine carries no data and no per-ARA config: it operates on a bare `<ara_dir>`, builds no
intermediate database or index, and has no write path (§4b).

---

## 2. Grounding references

Grounding is the ARA's **native anchors**, used **verbatim** — no minting, no `<scheme>://…` strings.
Every assertion a contract emits carries one or more of these refs:

| what is referenced | native ref form | example |
|---|---|---|
| trace node | `trace:<Nxx>` | `trace:N109` |
| claim | `logic/claims.md#<Cxx>` | `logic/claims.md#C05` |
| concept | `logic/concepts.md#<name>` | `logic/concepts.md#warmup-schedule` |
| method / problem | `<file path>#<section>` | `logic/solution/method.md#step-3`, `logic/problem.md#objective` |
| evidence | `evidence/.../<file>.md` | `evidence/figures/figure3.md` |

**Ref-honesty rule.** A ref is a *promise* that the cited location actually contains the claim it is
attached to. A contract may not attach a ref it has not read and confirmed; an assertion with no
resolvable ref is not allowed (§4a).

**Multi-ARA hook (design only, not built now).** Single-ARA refs are the zero-prefix case — in single-ARA operation the prefix is simply omitted: `trace:N109`, `logic/claims.md#C05`. A later
multi-ARA layer disambiguates by ARA name (`<ara_name>:trace:N109`); the contracts say "the ARA in
scope", so no field is renamed to add it.

---

## 3. What each contract reads and writes

| contract | reads | writes |
|---|---|---|
| `RETRIEVE.md` | the ARA's native files directly (`logic/`, `trace/`, `evidence/`, `src/`, `PAPER.md`) | **nothing** |
| `PREDICT.md` | answers any question over the ARA, grounded in native refs (via `RETRIEVE.md`) | **nothing** |

`RETRIEVE.md` is **not** limited to `experiment`/`dead_end` nodes — `question`/`decision`/`pivot`
nodes, `problem.md` framing, the `solution/` method, and evidence figures are all in scope and are
often the highest-value context.

---

## 4. Invariants

These bind every module; a contract that cannot satisfy one must say so rather than violate it.

a. **Forced native-ref grounding.** Every assertion a contract emits carries one or more native
   refs (§2) that resolve into the ARA in scope. No resolvable ref ⇒ the assertion is not made.

b. **The engine never writes.** Every contract (`RETRIEVE.md`, `PREDICT.md`) produces output only;
   the World Model writes nothing into the ARA — not `logic/`, not `trace/`, not `staging/`, nowhere.
   Write-back into the ARA's canonical `logic/` is owned by the ARA's own `research-manager`.

c. **No domain branching.** No rule or inference keys on a domain, metric, or parameter name;
   domain specifics enter only as data read from the ARA in scope.

d. **Honest disclosure.** Uncertainty is disclosed, never suppressed: the Retriever lowers its
   coverage verdict when the ARA does not cover the query, and the Predictor lowers confidence
   for any answer beyond what its cited refs support — a low-confidence bold answer is allowed;
   a confident ungrounded one is not.
