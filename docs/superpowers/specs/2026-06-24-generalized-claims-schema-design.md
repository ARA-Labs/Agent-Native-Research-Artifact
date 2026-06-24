# Generalized Claims Schema — Design Spec

- **Date**: 2026-06-24
- **Status**: approved design, pending implementation
- **Scope**: `skills/compiler` + `skills/research-manager` only. `rigor-reviewer` deliberately
  out of scope (deferred). No new artifact layer.
- **Owner**: chengysh

---

## 1. Problem

ARA `logic/claims.md` claims come out **narrow and numerical**. The subject of every claim is a
named recipe and the predicate is a number on a frozen benchmark, e.g.:

> "proj-only Aurora on the C04 stack passes `(3.28−μ)·√n ≥ 0.004` at ts3037, n=8, +0.006074;
> sub-3037 fails."

This is a *leaderboard coordinate*, not a piece of transferable knowledge. The genuinely intuitive,
reusable content ("leverage-aware preconditioning helps wide matrices, hurts tall ones") exists
inside these claims but only as a buried sub-clause.

### Root cause (located in the skill design, not in claim-writing)

The narrowness is the **conservatism axiom** working as designed:

- `skills/compiler/references/ara-schema.md` — *"Statement should stay at the strongest level
  directly supported by the cited evidence. Use Interpretation for broader synthesis."*
- `skills/compiler/SKILL.md` (Rule 10) — *"Evidence-limited wording: don't use stronger language
  than the evidence supports; separate observation from interpretation."*
- `skills/research-manager/SKILL.md` — the **live** Claim schema dropped the `Interpretation` field
  entirely, so in turn-by-turn mode the generalization has *no field to live in* and gets crammed
  into `Statement`.
- The crystallization closure signals are all **result events** (empirical-resolution = a stat-pass,
  artifact-commitment = a commit), so claims crystallize around the number that just resolved.

This axiom is correct for **compiling a published paper** (faithful transcription must not
over-reach). It is wrong for ARA used as a **generative knowledge instrument** for live research,
where it collapses every canonical claim onto the most evidence-proximate object — a number.

## 2. Decision

The generalization should **be the claim's `Statement`**, not a restatement of run numbers sitting
beside it. Numbers leave the claim body and live in `Proof` → `evidence/results/` (which already
exists). What keeps the generalized claim falsifiable and honest is a new **`Conditions`** field
("under what conditions it holds") plus a **substantive `Falsification`** (about the system, or about
the benchmark's behavior for a methodological claim), not a narrow numeric Statement.

Settled design choices:

- **Field-on-claim, NOT a new layer.** No `logic/insights.md`. The change is to what a `Statement`
  *is*, plus one new field.
- **`Statement` = the generalized, mechanistic conclusion.** Subject is a mechanism / relationship,
  never a named recipe. No run IDs, n-counts, or scores in the Statement.
- **`Conditions` (new field)** = under what conditions the conclusion holds, and the known untested
  boundary. This replaces the old "narrow Statement" as the device that keeps the claim accountable.
- **`Falsification` is substantive (not narrowly "mechanistic")** — a concrete observation that
  would break it: about the system/world for a mechanism claim, or about the benchmark's behavior for
  a methodological/regime claim (e.g. "single-seed crossings reliably reproduce"). Still forbidden:
  tautologies and same-gate re-runs ("if the recipe fails the gate"). *[Refined after the first
  compile test — methodological claims (the statistical-gate-as-result type) were being forced to
  fake a physical mechanism.]*
- **Calibrate the Statement to what the evidence separates** — don't assert a distinction the design
  confounds (co-varying factors, e.g. matrix "shape" vs "role"), or a law from a single instance;
  hedge that in the Statement itself, not only in `Conditions`. `Conditions` bounds *where* a claim
  holds; it is not a license for the Statement's verb to over-reach. *[Added after the first compile
  test — generalized Statements were reading slightly stronger than the evidence licensed.]*
- **Numbers → `Proof` / `evidence/results/`.** Grounding by reference, not restatement.
- **`rigor-reviewer` unchanged** for now (its D2/D3/D6 pressure toward narrowness, and a possible D7
  Transferability dimension, are a separate follow-up).
- **`wm-distill` / `wm-predict` unchanged structurally** — they gain a more useful `Statement`/
  `Conditions` to retrieve on as a pure dividend.

The conservatism that made ARA trustworthy is **preserved but relocated**: from "narrow the
sentence" to "state the generalization + write the full `Conditions` + keep `Falsification`
substantive + calibrate the Statement to what the evidence separates + keep numbers traceable in
`Proof`."

## 3. New claim schema

```markdown
## C{NN}: {generalized title — the takeaway, not a recipe name}
- **Statement**: {the generalized mechanistic conclusion; subject = a mechanism/relationship;
  no run numbers}
- **Conditions**: {under what conditions it holds; the regime; the known untested boundary}
- **Status**: hypothesis | testing | supported | weakened | refuted | withdrawn
- **Provenance**: user | ai-suggested | user-revised
- **Falsification**: {a concrete observation that disproves it — about the system for a mechanism
  claim, about the benchmark's behavior for a methodological one; not a tautology/gate re-run}
- **Proof**: [→ evidence/results/… and trace nodes; the numbers live here, not in Statement]
- **Dependencies**: [C{YY}, ...]
- **Tags**: {comma-separated}
- **Last revised**: YYYY-MM-DD (turn-id)   # absent until first revision
```

Notes:
- `Conditions` is mandatory. A generalized Statement with no `Conditions` is the failure mode this
  schema exists to prevent (unbounded slogan).
- `Statement` may be sharpened over later turns by Stage-4 reconciliation as the mechanism becomes
  clearer — this uses the existing content-revision machinery; **no new closure signal is required.**

## 4. Worked examples

### 4a. Mechanism takeaway (was: C06 / Aurora)

- **Statement**: When a row-leverage-uniformity correction (Aurora-style) is added on top of an
  orthogonalizing matrix optimizer (Muon family), applying it **by matrix shape** — only where
  columns outnumber rows (wide MLP `proj`, m<n), not to tall matrices and not globally — is what
  makes it help. On tall matrices (`fc`, m>n) the same correction hurts, and an all-shapes mask
  cancels to no net gain. The deciding factor is the matrix shape it is applied to, not which
  optimizer family it rides on.
- **Conditions**: rectangular MLP weight matrices under a Muon-family orthogonalizing update; the
  proj/fc aspect-ratio split; verified on this nanogpt speedrun, one architecture. Untested on
  attention matrices or other aspect ratios.
- **Falsification**: breaks if an all-rectangular mask matches shape-selective application at equal
  budget, or if a tall-matrix-only application ever helps, or if the proj/fc asymmetry vanishes at a
  different aspect ratio.
- **Proof**: `evidence/results/c06_aurora_projonly_statpass.md` (mask ablation: proj-only passes the
  gate, all-rect near-miss, fc hurts).

The forbidden form (what we are moving away from): *"proj-only Aurora passes the gate at ts3037,
n=8, +0.006074; sub-3037 fails."*

### 4b. Methodological / negative takeaway (was: cc-raw C03 → C05)

- **Statement**: A mathematically "near-equivalent" forward-path precision change can manufacture an
  apparent benchmark win that does not survive a byte-identical-compliant rebuild. Striking gains
  must first be ruled out as compliance/precision artifacts before being attributed to a mechanism.
- **Conditions**: bf16 forward paths where a norm/precision rewrite (e.g. RMSNorm / q-k-norm)
  silently shifts numerics; any benchmark with a frozen-architecture compliance rule.
- **Falsification**: breaks if rebuilding the recipe on a byte-identical-Architecture base preserves
  the win under the same statistical gate.
- **Proof**: `evidence/results/c03_ccv12_stepcount_frontier.md`, `c04_legal_v12opt_statpass.md`.

## 5. File-level changes

### 5a. `skills/research-manager/SKILL.md`

**Edit 1 — Claim schema.** Add `Conditions`; reword `Falsification`'s intent; state numbers belong
in `Proof`.

- Before: schema with `Statement / Status / Provenance / Falsification criteria / Proof /
  Dependencies / Tags / Last revised`.
- After: insert `- **Conditions**: {regime + untested boundary}` after `Statement`; rename
  `Falsification criteria` → `Falsification` with intent "a substantive observation that disproves it
  — about the system, or about the benchmark's behavior for a methodological claim; not a tautology /
  gate re-run"; add a one-line rule under the schema: *"Statement is the generalized conclusion
  (mechanism/relationship as subject), carries no run numbers; numbers live in Proof → evidence/"*;
  add the Statement-calibration paragraph (confounded factors / single-instance hedge).

**Edit 2 — Stage 4 reconciliation (content-revision bullet).** Add: when a claim is reconciled,
keep `Statement` a generalized mechanism/relationship and sharpen `Conditions`; new run numbers
update `Proof`/`evidence`, never the Statement.

### 5b. `skills/compiler/references/ara-schema.md`

**Edit 3 — `logic/claims.md` section.** Replace the schema block: `Statement` defined as the
generalized conclusion; add mandatory `Conditions`; `Falsification criteria` → substantive (system-
or benchmark-level); drop `Interpretation` (its role is absorbed into the generalized `Statement` +
`Conditions`); keep `Evidence basis` pointing at evidence with no numeric restatement in Statement.
Update the prose from *"Statement should stay at the strongest level directly supported"* to the new
rule, and add the Statement-calibration paragraph.

### 5c. `skills/compiler/SKILL.md`

**Edit 4 — Stage 2 claims bullet.** Reword from "Phrase each Statement at the strongest level the
cited evidence directly supports; keep raw support in Evidence basis and broader synthesis in
Interpretation" → "Phrase each Statement as the **generalized conclusion** the evidence supports
(mechanism/relationship as subject, no run numbers); bound it with **Conditions**; keep numbers in
evidence and reference them in Proof; calibrate the Statement to what the evidence separates."

**Edit 5 — Rule 10.** Reword to "Generalize, then bound — but only as far as the evidence separates":
the new accountability is `Conditions` + substantive `Falsification` + Statement-calibration +
grounded `Proof`, not a narrowed sentence.

**Edit 6 — Seal Level 1 claim-field check + `validation-checklist.md`.** Require `Conditions`;
required field list `Interpretation` → `Conditions`; Statement = generalized mechanism (no run
numbers); add a Statement-calibration check.

### 5d. `skills/research-manager/references/event-taxonomy.md`

**Edit 7 — routing tree.** The `claim` branch: "Falsifiable assertion about the system?" →
"Generalizable falsifiable assertion (a mechanism/relationship, bounded by conditions)?"

## 6. Non-goals / out of scope

- No `logic/insights.md` or any new layer.
- No new closure signal in research-manager.
- No `rigor-reviewer` changes (D7 Transferability and the D3 over-claiming reword are a separate
  follow-up; without them the reviewer may under-reward generalized claims — accepted for now).
- No new `Status` rung — the existing `hypothesis | testing | supported | weakened | …` ladder is
  unchanged. (A `strongly supported` rung to register corroboration breadth was prototyped and
  reverted; deferred.)
- No change to the **number-grounding** discipline (the `Sources` field, the "Number grounding"
  subsection, Rule 16). It is orthogonal — an anti-fabrication rule for any number you *do* write. It
  is preserved verbatim; the only adjustment is that its target broadens from "number in `Statement`"
  to "number in the claim", since numbers now live in `Conditions`/`Proof`/`Evidence basis` rather
  than the `Statement`.
- No `wm-*` structural changes.
- Regenerating the existing example ARAs (`ARA-Demo`, the speedrun pipelines) to the new schema is
  **downstream consumption**, not part of this skill change.

## 7. Validation

- The two skill schema blocks are internally consistent (compiler ara-schema ↔ research-manager live
  schema use the same field names: `Statement / Conditions / Falsification / Proof`).
- A re-read of compiler Rule 10 and Stage 2 no longer instructs narrowing the Statement.
- Spot-check by rewriting one real claim (C06) against the new schema (done — §4a) and confirming no
  run numbers appear in `Statement` and `Conditions` is non-trivial.
