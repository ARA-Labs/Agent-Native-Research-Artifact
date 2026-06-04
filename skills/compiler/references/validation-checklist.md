# ARA Seal Level 1 — Validation Checklist

These are all checks the Seal validator runs. Fix ALL failures before reporting success.

Validation is **profile-aware**. First read `ara_profile` and `profile_manifest` from PAPER.md.
Check the **Universal Core** (always) plus every file in `profile_manifest`. Profile-specific
files and the cross-layer checks that depend on them apply only when the active profile includes
them. See `domain-profiles.md`.

## 1. Directory Existence

Universal Core dirs — all must exist:
- `logic/`
- `logic/solution/`
- `src/`
- `trace/`
- `evidence/`

Profile-conditional dirs — required only when the active profile uses them:
- `src/configs/` (ml-model, ml-eval, systems)
- `data/` (data-science)
- `evidence/proofs/` (theory)

## 2. Mandatory File Existence (non-empty)

### 2a. Universal Core — always required (>10 bytes)
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
- ≥1 evidence file in `evidence/tables/`, `evidence/figures/`, or `evidence/proofs/`

### 2b. Profile manifest — every path in PAPER.md `profile_manifest` (>10 bytes)
The domain-specific method/artifact files, defined by `ara_profile` (see `domain-profiles.md` for
each profile's list). Check that every manifest path exists and is non-empty. Model-training files
(`training.md`/`model.md`) should not appear unless the work actually trained a model.

## 3. PAPER.md Checks

- Starts with `---` (YAML frontmatter)
- Frontmatter is valid YAML mapping
- Contains keys: `title`, `authors`, `year`
- Contains `ara_profile` (a starter name or a synthesized name)
- Contains `profile_manifest` (a non-empty list of profile-specific file paths)
- Every path in `profile_manifest` exists and is non-empty (drives check 2b)
- Body contains "Layer Index" section

## 4. Field-Level Checks (regex patterns)

### logic/claims.md
- Has `## C\d+` blocks (at least one claim)
- Contains `**Statement**`
- Contains `**Status**`
- Contains `**Falsification criteria**`
- Contains `**Proof**`
- Contains `**Evidence basis**`
- Contains `**Interpretation**`

### logic/problem.md
- Has `### O\d+` blocks (observations)
- Has `### G\d+` blocks (gaps)
- Has Key Insight section (`## Key Insight` or `**Insight**`)

### logic/experiments.md
- Has `## E\d+` blocks (at least 3)
- Contains `**Verifies**`
- Contains `**Setup**`
- Contains `**Procedure**`
- Contains `**Expected outcome**` or `**Expected results**`

### logic/solution/heuristics.md (only when in the active profile's manifest)
- Has `## H\d+` blocks
- Contains `**Rationale**`
- Contains `**Sensitivity**`
- Contains `**Bounds**`

### logic/solution/ profile method files
- The method files named in `profile_manifest` exist and are non-trivial (e.g. ml-model:
  architecture.md + algorithm.md; data-science: study_design.md + analysis_plan.md; theory:
  formalization.md + results.md + proofs.md)
- `logic/solution/constraints.md` exists regardless of profile (Universal Core)

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
- `src/execution/`: ≥1 `.py` file — only when the active profile includes a code artifact (not required for theory, or for non-code generic work that uses `src/artifacts.md`). NOT mandatory when the source has no implementable content; omitting it (with a note in `environment.md`) beats fabricating one.
- `evidence/tables/`, `evidence/figures/`, or `evidence/proofs/`: ≥1 `.md` file

### Code grounding (each `src/execution/*.py`, when present)
- Declares a `# Grounding: transcribed|reconstructed|interface-only` tag
- Docstrings cite the source (§/Eq/repo path), not paraphrases of the compiler skill
- `interface-only` / unspecified bodies are `NotImplementedError("Not specified in paper")`, not invented logic
- FAIL if the file invents API names, constants, or function bodies with no traceable source — a hollow fabricated API must be omitted, not shipped

## 5b. Appendix Coverage

When the source has appendices, every appendix section should be traceable to at least
one ARA file, with the granularity of the source preserved.

## 6. Evidence Quality

For each file in `evidence/tables/*.md` and `evidence/figures/*.md`:
- Must contain `**Source**` field
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
- Claim wording should be auditable against `Evidence basis`; broader language should be isolated to `Interpretation`

### Experiment Verifies → Claim Resolution
- Every `C\d+` in an experiment's `**Verifies**` must exist in claims.md

### Heuristic Code Ref → File Resolution (only when heuristics.md + src/execution/ are both in the profile)
- Every `src/...` path in `**Code ref**: [...]` must be an existing file

### Architecture Components → Code Stubs (fuzzy; only when architecture.md + src/execution/ are both in the profile)
- Significant words from `## ` headings in architecture.md should appear somewhere in src/execution/ code

### Tree Evidence → Claims (YAML)
- Any `C\d+` in a tree node's `evidence` field must exist in claims.md

### Trace Hygiene
- Do not add dead_end, decision, or experiment nodes that are unsupported by the provided source material
- If a node is reconstructed from partial evidence rather than stated explicitly, it should be marked as inferred or excluded from Seal Level 1 outputs
