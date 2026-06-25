# ARA Seal Level 1 — Validation Checklist

These are all checks the Seal validator runs. Fix ALL failures before reporting success.

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
- Has `## C\d+` blocks (at least one claim)
- Contains `**Statement**` (the mechanism/takeaway a result reveals — subject is a mechanism/relationship, never a named recipe; no run numbers)
- Contains `**Conditions**` (non-trivial: the regime + the untested boundary)
- Contains `**Sources**`; every load-bearing number in a claim has a `Sources` entry carrying
  a verbatim «quote» plus an `[input]`/`[result]` tag — no bare-path entries, no memory-filled numbers
- Contains `**Status**`
- Contains `**Falsification criteria**` (a substantive observation — about the system, or about the benchmark's behavior for a methodological claim — not a tautology or a re-run of a metric gate)
- `Statement` is the mechanism/takeaway a result reveals, not a record: a single instance may state the mechanism it reveals, but must not be extrapolated into a universal law beyond its regime, nor assert a distinction the design cannot disentangle — those limits live in `Conditions`
- Contains `**Proof**`
- Contains `**Evidence basis**`

### logic/problem.md
- Has `### O\d+` blocks (observations)
- Has `### G\d+` blocks (gaps)
- Has Key Insight section (`## Key Insight` or `**Insight**`)

### logic/experiments.md
- Has `## E\d+` blocks (at least 3)
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
- Has `## ` sections (at least 5)
- Contains `**Definition**`

## 5. Count Checks

Counts are **source-bounded targets, not quotas** (Rule 14): they must be met from genuine source
content, never by padding with trivial, borrowed, or invented items. A paper that honestly supports
fewer passes with fewer; what fails is fabricated filler.

- `logic/concepts.md`: aim ≥5 concept sections (`## ` headers) — but only genuine technical terms
- `logic/experiments.md`: aim ≥3 experiment/analysis blocks (`## E\d+`) — only experiments the paper actually describes
- `src/execution/`: ≥1 `.py` file only when the work has implementable content (repo code / paper pseudocode / named interface). NOT mandatory otherwise; omitting it (with a note in `environment.md`) beats fabricating one.
- `evidence/tables/`, `evidence/figures/`, or `evidence/proofs/`: contains the filed evidence (see §11)

### Implementation layer (`src/`) — captured, not re-encoded
- Concrete artifacts that exist are captured in native form: prompts/templates verbatim in `src/prompts/`, **real repo source code captured into `src/execution/`** (native form, `# Grounding: transcribed`, cite path — not reduced to a pointer), non-code deliverables (released binaries, skill/spec docs, referenced datasets) described in `src/artifacts.md`, config values in `src/configs/`. A lone `environment.md` is wrong when such artifacts exist.
- **When a code repo/directory was provided as input**: every non-trivial runnable source file in it (a named module, entrypoint, or roughly ≥30 lines) is captured into `src/execution/` (or another `src/` subdir, in native form), not merely named in `artifacts.md`. FAIL on real source code represented only by a pointer, or a set of real files dismissed collectively (e.g. "not a core contribution") without capture.
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
- Every `E\d+` in a claim's `**Proof**: [...]` must exist in experiments.md
- Proof-linked experiments should have evidence files whose labels and row contents actually match the compared systems or measurements
- Claim `Statement` is a generalized mechanism/relationship auditable against `Evidence basis`; its reach is bounded by `Conditions` and its run numbers live in the evidence layer (not pasted into the Statement)

### Experiment Verifies → Claim Resolution
- Every `C\d+` in an experiment's `**Verifies**` must exist in claims.md

### Experiment Evidence / Run → Resolution
- Every `evidence/…` path in an experiment's `**Evidence**` is a filed evidence file (or "pending")
- Every experiment carries a `**Run**` ref — a real `src/execution/` file or an entry in the run ledger `src/execution/artifacts.md` that links the source-DB location; failed/ablated runs are linked there, not dropped

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
- **Claim Statements are takeaways** (exhaustive, not spot-checked — symmetric to the number-sources
  pass): each `## C\d+` Statement FAILS if its subject is a named recipe/config/run, or if it
  contains a run number, n-count, score, step/bin count, or p-value. The mechanism a result reveals
  must be the subject; the numbers must live in `Evidence basis`/`Proof`
- **Attribution is not insight** (exhaustive, applied to each Statement that already passed the
  takeaways gate above): a Statement also FAILS if it only identifies *which* named components of
  this one system rank highest/lowest (load-bearing / dominant / decorative / inert / "largest
  contributor") without stating what that ranking *reveals* — a relationship or mechanism a reader
  could carry to a different system. **Operational tell: delete this system's component names from
  the Statement; if no transferable relationship survives, it is attribution, not a mechanism — it
  FAILS.** The fix is to state the generalization the ranking licenses; the named components and
  their deltas stay in `Evidence basis`. This is the most common way a numerically-clean Statement
  still fails the insight bar.
- **Claim/heuristic number sources** (exhaustive, not spot-checked): each `**Sources**` entry's cited
  `file:line` (or trace `node:field`) exists, the verbatim «quote» is actually present there, and the
  number in the `Statement`/`Rationale` matches the value inside that quote; `[input]` entries cite
  recipe scripts and `[result]` entries cite run logs/trace (not swapped). A bare path with no «quote»,
  a «quote» absent from the cited line, or a value that disagrees with its quote FAILS. `[pending: …]`
  entries pass but are listed for follow-up — an unverified plausible path does not pass

## 11. Evidence Ledger Completeness

- **Every numbered `Table N` and `Figure N` in the source is filed** — a complete, in-order sweep,
  not a sample. Each filed object has BOTH a markdown file and a screenshot `.png`.
- Every value a claim quotes traces to a filed table/figure.
- Any numbered object deliberately not filed (e.g. an exact duplicate) is listed in
  `evidence/README.md` with a reason — no silent omissions. A run that quietly filed only some of
  the source's tables/figures FAILS.

## 12. Self-Consistency

- Any ARA-authored derived number (a delta, percentage, or comparison the ARA computes itself) recomputes correctly from its cited cells
- `PAPER.md` frontmatter/Layer-Index declared counts (claims, concepts, experiments, …) match the actual files
- Tree `evidence:` references are claim IDs (`C\d+`), not observation IDs (`O\d+`) or other layers
