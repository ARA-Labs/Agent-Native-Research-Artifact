# ARA Seal Level 1 — Validation Checklist

Load the local [property-authoring contract](property-authoring.md) before reviewing claims.
This checklist covers structural checks and source-faithful authoring review. Record the actual
Seal validator's output separately; structural acceptance does not certify source fidelity or
an executable check. Fix failures without inventing support or weakening an assertion.

## 1. Directory Existence

Mandatory-core dirs — all must exist: `logic/`, `logic/solution/`, `src/`, `trace/`, `evidence/`.
Other dirs (`src/configs/`, `data/`, `evidence/proofs/`, …) exist only when the work warrants them.

## 2. Mandatory File Existence (non-empty, >10 bytes)

- `PAPER.md`
- `logic/problem.md`
- `logic/claims.md`
- `logic/concepts.md`
- `logic/experiments.md`
- `logic/solution/constraints.md`
- `logic/related_work.md`
- `src/environment.md`
- `trace/exploration_tree.yaml`
- `evidence/README.md`
- an evidence file for every numbered table and figure (see §11)

Additional method/artifact files (`logic/solution/*`, `src/*`, `data/*`) are validated only that,
where present, they are non-trivial — there is no fixed list. Model-training files
(`training.md`/`model.md`) should not appear unless the work actually trained a model.

## 3. PAPER.md Checks

- Starts with `---` (YAML frontmatter); valid YAML mapping
- Contains keys: `title`, `authors`, `year`
- Body contains "Layer Index" section

## 4. Field-Level Checks (regex patterns)

### logic/claims.md
- Has source-supported `## C\d+` blocks; if none are warranted, state why and retain staged
  obligations in the all-selected-assertions ledger rather than inventing a claim
- Contains `**Statement**` preserving the verbatim source assertion; named configurations,
  bounded empirical comparisons, and source-grounded numerical assertions are allowed
- Contains `**Conditions**` preserving scope, units, quantifier, aggregation, statistical unit,
  uncertainty, and untested boundaries; missing details are attributed unknowns
- Contains `**Sources**`; the assertion has its source revision/anchor and verbatim quote, and
  every load-bearing number has a quoted `[input]`/`[result]` entry, or an explicit pending reason
- Contains `**Status**` reflecting actual support, not spec acceptance or a holding check
- Contains `**Falsification criteria**` addressing the actual assertion; a contradicted required
  ordering is meaningful for a bounded comparison; unavailable criteria are explicit
- Keeps synthesis in a separately identified claim linked to the preserved assertions; no
  forced mechanism inference from one result or component ranking
- Contains `**Proof**` with only real relevant experiment IDs, or `pending` plus a missing-support reason
- Contains `**Evidence basis**` with neutral evidence references, conflicts, and gaps, not authored
  candidate relations, selected operands, check results, or review/repair answers

### logic/problem.md
- Has `### O\d+` blocks (observations)
- Has `### G\d+` blocks (gaps)
- Has Key Insight section (`## Key Insight` or `**Insight**`)

### logic/experiments.md
- Has source-supported `## E\d+` blocks (aim for 3 only when warranted); record fewer or none
  with a reason, never invent an experiment to fill a count or a claim's Proof
- Contains `**Verifies**`
- Contains `**Evidence**` (link to where the run's results are filed, or "pending")
- Contains `**Run**` (what produced the run — a `src/execution/` file or a link/ref into the source repo/DB; failed/ablated runs are linked too, not omitted)
- Contains `**Setup**`
- Contains `**Procedure**`
- Contains `**Expected outcome**` or `**Expected results**`

### logic/solution/heuristics.md (when present)
- Has `## H\d+` blocks
- Contains `**Rationale**`
- Contains `**Sensitivity**`
- Contains `**Bounds**`

### logic/solution/ method files
- `logic/solution/constraints.md` exists (mandatory core)
- Whatever other method files the work warrants (architecture/algorithm/method/study_design/
  formalization/proofs/…) exist and are non-trivial — there is no required set

### logic/related_work.md
- Has `## RW\d+` blocks
- Contains `**Type**`
- Contains `**Delta**`
- Coverage should extend beyond the closest predecessors to reflect the paper's full
  citation footprint

### logic/concepts.md
- Has genuine concept `## ` sections (aim for 5 only when warranted); record the shortfall
- Contains `**Definition**`

## 5. Count Checks

Counts are **source-bounded targets, not quotas** (Rule 15). Fewer or no supported items require
a stated reason, not fabricated filler. A missing proof remains missing; unsupported selected
assertions stay in the ledger whether or not they have claim blocks or executable declarations.

- `logic/concepts.md`: aim ≥5 concept sections (`## ` headers) — but only genuine technical terms
- `logic/experiments.md`: aim ≥3 experiment/analysis blocks (`## E\d+`) — only experiments the paper actually describes
- `src/execution/`: ≥1 `.py` file only when the work has implementable content (repo code / paper pseudocode / named interface). NOT mandatory otherwise; omitting it (with a note in `environment.md`) beats fabricating one.
- `evidence/tables/`, `evidence/figures/`, or `evidence/proofs/`: contains the filed evidence (see §11)

### Implementation layer (`src/`) — indexed when external, captured when it'd be lost
- Concrete artifacts are represented losslessly: prompts/templates verbatim in `src/prompts/`, config values in `src/configs/`, and — when the work's code/runs **persist in a linkable external store** — a **comprehensive pointer index** in `src/artifacts.md` linking every artifact. A lone `environment.md` is wrong when such artifacts exist.
- **Comprehensiveness** (external repo/run-database input): `src/artifacts.md` links **every** run and source file (per-run logs included — a `runs.jsonl` counts), nothing aggregated into a bare directory link or a "~N others" summary. FAIL on a lossy subset (only the winning run; real artifacts collapsed into a vague bucket).
- **Capture only when it'd be lost**: transcribe source into `src/execution/` (native form, `# Grounding: transcribed`, cite path) only when it exists solely inside the paper or its source is not externally persisted. Pointer-only is correct when the source persists; it FAILS only when the pointer would dangle (no persisted source).
- Conversely, a prose-only method (no code, no prompt, no config values) is NOT re-encoded as a `.py` stub or pseudo-code — it lives in `logic/solution/`; a lone `environment.md` is correct here. FAIL on a `.py` stub manufactured from prose (it just duplicates the cognitive layer).

### Code grounding (each `src/execution/*.py`, when present)
- Declares a `# Grounding: transcribed|reconstructed` tag
- Docstrings cite the source (§/Eq/repo path), not paraphrases of the compiler skill
- FAIL if the file invents API names, constants, or function bodies with no traceable source — a hollow fabricated API must be omitted, not shipped

## 5b. Appendix Coverage

When the source has appendices, every appendix section should be traceable to at least
one ARA file, with the granularity of the source preserved.

## 6. Evidence Quality

For each file in `evidence/tables/*.md` and `evidence/figures/*.md`:
- Must contain `**Source**` field
- **Must have a sibling screenshot `.png`** (e.g. `table3.md` ↔ `table3.png`, `figure5.md` ↔ `figure5.png`), declared via a `**Screenshot**` field
- Table files must contain a Markdown table (`|...|...|` pattern)
- If the filename includes `table{N}` or `figure{N}`, the `**Source**` field must reference the same identifier
- If the file is a derived subset, it must say so explicitly via `**Extraction type**: derived_subset` or equivalent
- Raw source-table files should not silently omit rows while still presenting themselves as the original table

For each file in `evidence/figures/*.md` specifically:
- Must declare `**Figure type**` in {quantitative_plot, diagram, qualitative_sample, mixed}
- Must declare `**Extraction method**` in {exact_from_labels, digitized_estimate, visual_description} and `**Reading confidence**` in {high, medium, low}
- `quantitative_plot` figures must contain either a Markdown data table OR an explicit unreadable statement with `Reading confidence: low` plus a `Trend summary`; their `**Axes**` field must state the scale (linear/log)
- `diagram` and `qualitative_sample` figures must contain a `Visual description` section and must NOT present a fabricated numeric data table
- Any estimated numeric reading should be marked approximate (`≈`) and the file's extraction method should be `digitized_estimate` (not `exact_from_labels`)
- Preserve original headers, axis order, exact method variants, metric identities, units, task
  scope, aggregation, and uncertainty annotations. Unresolved headers and aliases stay unresolved;
  an alias must not merge fixed and adaptive variants. Absent variance is not zero.

## 7. evidence/README.md

- Must contain a Markdown table (file index)
- Numbered tables and figures from the source (main text and appendices) should be
  reflected in the index

## 8. Exploration Tree (YAML)

- Parses as valid YAML
- Has top-level `tree` key
- ~8+ nodes is the target for a rich paper, but a smaller fully source-backed tree PASSES — do not flag low counts that reflect a paper genuinely exposing little exploration (Rule 14). What fails is invented/unsupported nodes (see Trace Hygiene), not honest small trees.
- All node types in {question, decision, experiment, dead_end, pivot}
- `dead_end` / `decision` nodes are expected when the paper reveals ablations, rejected alternatives, or design choices — but are NOT required if the source exposes none; never invent one to satisfy this check (Rule 9)
- Every node has `id` and `type` fields
- Every node has `support_level` in {explicit, inferred}
- Type-specific required fields:
  - question: `description`
  - experiment: `result`
  - dead_end: `hypothesis`, `failure_mode`, `lesson`
  - decision: `choice`, `alternatives`
  - pivot: `from`, `to`, `trigger`
- All `also_depends_on` references resolve to existing node IDs
- Nodes with `support_level: explicit` should include `source_refs`

## 9. Cross-Layer Binding

### Claim Proof → Experiment Resolution
- Every `E\d+` in a claim's `**Proof**: [...]` must exist in experiments.md; `pending`
  with an explicit missing-support reason is preferable to invented experiments
- Proof-linked evidence must match the assertion's exact method variants, metrics, units,
  headers, task scope, aggregation, and every conjunct; mismatches remain explicit
- Audit the preserved Statement against its source anchor under the shared contract. Numerical
  assertions stay first-class; a separately linked synthesis must not replace the original.

### Experiment Verifies → Claim Resolution
- Every `C\d+` in an experiment's `**Verifies**` must exist in claims.md

### Experiment Evidence / Run → Resolution
- Every `evidence/…` path in an experiment's `**Evidence**` is a filed evidence file (or "pending")
- Every experiment carries a `**Run**` ref — an entry in the comprehensive `src/artifacts.md` index (or, in the capture-fallback case, a `src/execution/` file) that links the source location; failed/ablated runs are linked there, not dropped

### Claim Dependencies → Claim Resolution
- Every `C\d+` in a claim's `**Dependencies**` must exist in claims.md (an unresolved ID FAILS)

### Heuristic Code Ref → File Resolution (only when heuristics.md + src/execution/ are both present)
- Every `src/...` path in `**Code ref**: [...]` must be an existing file

### Architecture Components → Code Stubs (fuzzy; only when architecture.md + src/execution/ are both present)
- Significant words from `## ` headings in architecture.md should appear somewhere in src/execution/ code

### Tree Evidence → Claims (YAML)
- Any `C\d+` in a tree node's `evidence` field must exist in claims.md

### Trace Hygiene
- Do not add dead_end, decision, or experiment nodes that are unsupported by the provided source material
- If a node is reconstructed from partial evidence rather than stated explicitly, it should be marked as inferred or excluded from Seal Level 1 outputs

## 10. Citation Verification (Rule 15)

- Every repo path / `file:line` referenced (in `src/`, heuristic `Code ref`, environment "Code location") exists in the provided repo; no line reference points past the file's actual length
- No fact ABOUT a repo artifact (line count, path, internal structure) is transcribed from the paper without checking the real file — when paper and repo disagree, the discrepancy is flagged, not silently resolved to the paper's number
- Spot-check trace `source_refs` and evidence `**Source**` labels: the cited section/table/appendix actually contains the claimed content
- A statistic carries its scope/denominator (N, population) in its `Source` — subset figures (e.g. "5 papers / 3,050 reqs") are not juxtaposed with full-corpus figures as if same-denominator
- **Source-faithful Statements** (exhaustive, not spot-checked): compare each assertion with its
  source revision/anchor using [What must survive](property-authoring.md#what-must-survive).
  Fail omitted conjuncts, changed variants or metric headers, weakened all-tasks scope, invented
  uncertainty, or replacement of the assertion with a generalized explanation. Named methods,
  numbers, p-values, and component comparisons are not failures merely for appearing in a Statement.
  An unresolved field is recorded as unresolved, not silently selected to make a check hold.
- **Separate synthesis**: check that inferred explanations have their own identity and links to
  preserved assertions. Do not delete system names, demote quantitative assertions, or demand a
  transferable mechanism merely because a reported result or ablation is available.
- **Claim/heuristic number sources** (exhaustive, not spot-checked): each number-bearing `**Sources**` entry's cited
  `file:line` (or trace `node:field`) exists, the verbatim «quote» is actually present there, and the
  number in the `Statement`/`Rationale` matches the value inside that quote; `[input]` entries cite
  recipe scripts and `[result]` entries cite run logs/trace (not swapped). A bare path with no «quote»,
  a «quote» absent from the cited line, or a value that disagrees with its quote FAILS. `[pending: …]`
  entries pass but are listed for follow-up — an unverified plausible path does not pass

## 11. Evidence Ledger Completeness

- **Every numbered `Table N` and `Figure N` in the source is filed** — a complete, in-order sweep,
  not a sample. Each filed object has BOTH a markdown file and a screenshot `.png`.
- Every value a claim quotes traces to its filed source table, figure, log, or other allowed input;
  preserve approximation markers and uncertainty rather than inventing exactness
- Any numbered object deliberately not filed (e.g. an exact duplicate) is listed in
  `evidence/README.md` with a reason — no silent omissions. A run that quietly filed only some of
  the source's tables/figures FAILS.

## 12. Self-Consistency

- Any ARA-authored derived number (a delta, percentage, or comparison the ARA computes itself) recomputes correctly from its cited cells
- `PAPER.md` frontmatter/Layer-Index declared counts (claims, concepts, experiments, …) match the actual files
- Tree `evidence:` references are claim IDs (`C\d+`), not observation IDs (`O\d+`) or other layers

## 13. Property Authoring Boundaries

Apply the shared contract's [authoring order](property-authoring.md#author-in-this-order),
[revisions and check identity](property-authoring.md#revisions-and-check-identity), and
[isolated ARA-only extraction](property-authoring.md#isolated-ara-only-extraction) rules.

- The all-selected-assertions ledger retains the full source obligation and each unsupported
  reason. Distinguish no relation fit from no evidence; narrowed subclaims do not replace it.
- Review meaning against the captured assertion before any authorized execution. Record semantic
  review separately from schema acceptance, operand binding, execution outcome, and replay.
- Checks link the exact obligation version, declaration and evidence digests, catalog version,
  decision policy, and saved check record. After a semantic or policy revision, the prior check is
  historical only; retain initial and repaired candidates and their separate outcomes.
- When ARA-only extraction is requested, audit a pinned, allowlisted neutral view and its manifest.
  Keep preserved quotations, headers, scope, uncertainty, and unsupported obligations. Exclude the
  original packet and authoring/review answers, including transitive linked content, before giving
  a fresh extractor access. Merely asking it not to read excluded files does not isolate the view.
- Executable candidates use the contract's versioned `aratest/spec.yaml` format and production
  load/bind/check/save/replay APIs only when authorized and available. Missing runtime or unresolved
  obligations are explicit unperformed checks. This review authorizes no paid collection, fresh
  scientific run, catalog family campaign, or automatic retry loop.
