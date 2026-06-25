# ARA Directory Schema — Complete Field-Level Reference

## Directory Structure

`✓` = mandatory core (always present). Everything else is created **only when the paper's content
warrants it** — there is no domain template to fill; you decide which method/artifact files
genuinely represent the work. The layout below is illustrative, not prescriptive.

```
PAPER.md                            # ✓ Root manifest + layer index
logic/
  problem.md                        # ✓ Why: observations → gaps → key insight
  claims.md                         # ✓ Falsifiable assertions
  concepts.md                       # ✓ Key technical terms (one ## per term)
  experiments.md                    # ✓ Declarative verification/analysis plans (NOT scripts)
  solution/
    constraints.md                  # ✓ Boundary conditions + assumptions + limitations
    <method files>                  # as warranted: architecture / algorithm / method /
                                    #   study_design / formalization / results / proofs /
                                    #   design / heuristics … — whatever fits THIS work
  related_work.md                   # ✓ Typed dependency graph (RDO)
src/
  environment.md                    # ✓ Data/software/hardware/protocols/seeds
  configs/                          # as warranted: hyperparameters / inference / deployment
  execution/{module}.py             # as warranted: grounded code stub (or absent — see below)
  prompts/, ...                     # as warranted: prompt templates, etc.
data/                               # as warranted: dataset.md + preprocessing.md
trace/
  exploration_tree.yaml             # ✓ Research DAG: nested YAML tree with typed nodes
evidence/
  README.md                         # ✓ Index mapping every evidence file to claims
  tables/                           # ✓ every numbered Table: tableN.md + tableN.png
  figures/                          # ✓ every numbered Figure: figureN.md + figureN.png
  proofs/                           # as warranted: derivations / proofs
rubric/requirements.md              # (Only if a rubric is provided)
```

Every numbered table and figure in the source gets BOTH a markdown file and a screenshot `.png`
(see the evidence specs below). Additional files/subdirectories may be created on demand for
content that doesn't fit the standard layers (appendix worked examples, prompt templates,
taxonomies) — place such content where it best belongs.

## Progressive Disclosure (3 Levels)

- **Level 1 — PAPER.md** (~200 tokens): Frontmatter + layer index. Agent reads ONLY this to decide relevance.
- **Level 2 — Layer files** (problem.md, claims.md, experiments.md, evidence/README.md): Loaded on demand.
- **Level 3 — Detail files** (algorithm.md, code stubs, individual evidence tables): Loaded when drilling in.

---

## PAPER.md

YAML frontmatter MUST include:
```yaml
---
title: "{full paper title}"
authors: [{author list}]
year: {year}
venue: "{venue}"
doi: "{DOI or arXiv ID}"
ara_version: "1.0"
domain: "{research domain — free text}"
keywords: [{5-10 keywords}]
claims_summary:
  - "{one-line summary of each main claim}"
abstract: "{paper abstract}"
---
```

Body MUST include a Layer Index — a table for each layer listing every file actually generated:

```markdown
# {Paper Title}

## Overview
{1-2 paragraph summary of the contribution}

## Layer Index

### Cognitive Layer (`/logic`)
| File | Description |
|------|-------------|
| [problem.md](logic/problem.md) | Observations → gaps → key insight |
| [claims.md](logic/claims.md) | {N} falsifiable claims (C01–C{NN}) |
| ...

### Physical Layer (`/src`)
| File | Description | Claims |
|------|-------------|--------|
| [execution/{module}.py](src/execution/{module}.py) | {what} | C{NN} |
| ...

### Exploration Graph (`/trace`)
| File | Description |
|------|-------------|
| [exploration_tree.yaml](trace/exploration_tree.yaml) | {N}-node research DAG |

### Evidence (`/evidence`)
| File | Description |
|------|-------------|
| [README.md](evidence/README.md) | Full index of {N} tables + {N} figures |
```

---

## Evidence Naming and Fidelity

The evidence layer has two different object types:

1. **Raw source evidence**
   - Faithful transcription of one source table or figure
   - Must preserve the original source identifier and caption
   - Example: `evidence/tables/table3_imagenet_validation.md`

2. **Derived subset evidence**
   - Filtered or recomposed view created for a specific claim
   - Must NOT masquerade as the original source object
   - Filename should include `derived_`, `subset_`, or equivalent
   - Must declare which raw source object it came from
   - Example: `evidence/tables/derived_from_table3_residual_depth_slice.md`

Rule: if a filename includes a source label such as `table3` or `figure4`, it should faithfully represent that exact source object rather than a curated subset.

---

## logic/problem.md

```markdown
# Problem Specification

## Observations

### O{N}: {title}
- **Statement**: {precise empirical fact with numbers}
- **Evidence**: {source — figure, table, measurement, citation}
- **Implication**: {what this means for the problem}

## Gaps

### G{N}: {title}
- **Statement**: {what's missing or broken}
- **Caused by**: {which observations, e.g., O1, O2}
- **Existing attempts**: {what's been tried}
- **Why they fail**: {specific failure mode}

## Key Insight
- **Insight**: {the creative leap, stated precisely}
- **Derived from**: {which observations}
- **Enables**: {what solution approach this unlocks}

## Assumptions
- A1: {assumption}
- A2: {assumption}
```

---

## logic/claims.md

Each claim MUST have ALL fields:
```markdown
## C{NN}: {generalized title — the takeaway, not a recipe/result name}
- **Statement**: {the generalized, mechanistic conclusion the evidence supports; subject = a mechanism/relationship, never a named recipe; carries NO run numbers}
- **Conditions**: {under what conditions it holds; the regime; the known untested boundary}
- **Status**: {hypothesis|supported|refuted}
- **Falsification criteria**: {a concrete observation that would disprove it — for a mechanism claim, about the system/world; for a methodological/regime claim, about the benchmark's behavior. Not a tautology or a re-run of the same gate}
- **Proof**: [{experiment IDs: E01, E02}]
- **Evidence basis**: {what the cited evidence shows — point to it; do NOT restate run numbers in the Statement}
- **Dependencies**: {claim IDs this one rests on — the narrower claims a more general claim draws on, or a claim it corrects/refines; not mere shared setup; omit if it rests only on its own evidence}
- **Tags**: {comma-separated keywords}
```

Proof MUST reference experiment IDs from experiments.md.
Each proofed experiment should in turn be backed by evidence files whose rows or measurements actually match the claim being asserted.
`Statement` is the **generalized conclusion the evidence supports** — a mechanism or relationship,
not a restatement of run numbers. The claim is kept falsifiable and honest by `Conditions` (the
regime it holds in + the untested boundary) and a `Falsification criteria`, not by narrowing the
sentence to a single measured value. Numbers (n, scores, step counts, run IDs) live in the evidence
layer and are reached via `Proof`/`Evidence basis`, never pasted into `Statement`. `Conditions` is
mandatory: a generalized Statement with no Conditions is an unbounded slogan.

**Distill the mechanism; bound the reach.** Before writing a `Statement`, ask what the result
*reveals* — the mechanism or relationship a reader would reuse — and state that; the recipe and its
numbers are the evidence for it, not the claim, and never its subject. A single instance still
licenses a mechanism `Statement`; what is forbidden is extrapolating it into a universal law beyond
its regime, or asserting a distinction the design cannot disentangle. Put that boundary in
`Conditions` — it bounds *where* the claim holds and is not a license for the verb to over-reach.
`Conditions` carries the limits so the `Statement` can carry the mechanism.

**A claim's evidence may be one result or several read together.** Most claims distill what a single
result reveals; but where several experiments together reveal a relationship none shows alone —
whether they agree on it, or differ in a way that itself reveals what bounds or explains the
difference — that relationship is the claim. Write it as an ordinary `## C` block whose `Proof` lists
every experiment it draws on and whose `Dependencies` names the narrower claims it rests on; the same
distill-the-mechanism, bound-the-reach discipline applies. State the most general relationship the
evidence supports — bounded by `Conditions`, never asserted past what those experiments jointly show —
rather than settling for one claim per experiment. A claim need not be about the object under study:
a reusable relationship the work itself exposes, including in how it was run, is worth a claim.

**The attribution trap (the most common miss).** An ablation / leave-one-out that shows *which*
components dominate is the *evidence*, not the claim. A Statement that merely names the load-bearing
vs decorative components passes the no-numbers gate but is still a league table of *this* system.
Apply the **name-deletion test**: strike your system's component names from the Statement — if
nothing a stranger working on a different stack could reuse survives, you wrote attribution. State
instead what the ranking reveals about the *class* of system; the named components and their deltas
live in `Evidence basis`, reached via `Proof`.

---

## logic/concepts.md

Target ≥5 concepts, but capture the paper's *genuine* technical terms — don't pad with trivial or
borrowed terms to reach 5 (Rule 14). One section per concept:
```markdown
## {Term Name}
- **Notation**: {LaTeX or symbolic notation, or "—" if none}
- **Definition**: {Formal definition}
- **Boundary conditions**: {When it applies/not — or "Not specified in paper"}
- **Related concepts**: {other concept names}
```

---

## logic/experiments.md

≥3 experiments. Declarative plans, NOT scripts. NO exact numerical results. Experiments and claims
are **many-to-many**: one experiment may verify several claims, and a claim that generalises across
runs lists every experiment it draws on in its `Proof` — do not force a 1:1 claim↔experiment ledger.

```markdown
## E{NN}: {Short title}
- **Verifies**: {claim IDs this run bears on — may be several}
- **Evidence**: {evidence file(s) where this run's results are recorded — `evidence/…`; "pending" if not yet filed}
- **Run**: {what produced this result — a `src/execution/` file (or other `src/` artifact) when captured, else a link/ref into the source repo or run database; give it for EVERY experiment, including failed or ablated runs}
- **Setup**:
  - Model: {model name and size}
  - Hardware: {GPU type, count, memory}
  - Dataset: {dataset name, size, source}
  - System: {system configuration}
- **Procedure**:
  1. {Step 1}
  2. {Step 2}
- **Metrics**: {what to measure, with units}
- **Expected outcome**:
  - {directional/relative ONLY, e.g., "A outperforms B on metric X"}
  - NEVER exact numbers (those go in evidence/)
- **Baselines**: {methods to compare against}
- **Dependencies**: {other experiment IDs, or "none"}
```

---

## logic/solution/architecture.md

Component graph. For each component: name, purpose, inputs, outputs, interactions, key design choices.

## logic/solution/algorithm.md

- Mathematical formulation (LaTeX)
- Pseudocode (reconstruct only from the paper's stated algorithm; don't invent steps the paper omits)
- Step-by-step explanation
- Complexity analysis — only if the paper states or clearly implies it; else "Not specified in paper"

## logic/solution/constraints.md

- Boundary conditions
- Assumptions
- Known limitations

## logic/solution/heuristics.md

Include only heuristics the paper actually states (implementation tricks, convergence hacks,
practical gotchas). If the paper presents none, `heuristics.md` may be empty/omitted — do not invent
tricks. Each heuristic present uses these fields; values come from the paper, else "Not specified":
```markdown
## H{NN}: {Short description}
- **Rationale**: {Why this trick is needed}
- **Sensitivity**: {low|medium|high — or "Not specified in paper"}
- **Bounds**: {acceptable range or limits — or "Not specified in paper"}
- **Code ref**: [{path to src/execution/ file, or "Not specified"}]
- **Source**: {Section/table in the paper}
```

---

## logic/related_work.md

```markdown
## RW{NN}: {Author et al., Year}
- **DOI**: {DOI or arXiv ID}
- **Type**: {imports|bounds|baseline|extends|refutes}
- **Delta**:
  - What changed: {specific technical delta}
  - Why: {motivation}
- **Claims affected**: {claim IDs}
- **Adopted elements**: {what was kept}
```

Works with a specific technical delta get full `RW` blocks as above. Additional citations
from the paper that do not have a technical delta (background, historical, infrastructure,
or inline-comparison references) should still be captured more briefly so the ARA preserves
the paper's full citation footprint.

---

## src/configs/{config}.md  (when the work warrants it)

Name configs for what the work actually has — e.g. `training.md`/`model.md` for a trained model,
`inference.md` for an eval/prompting method, `deployment.md` for a system. Don't create
model-training configs for work that trained no model. All config files share one per-parameter
field format:

```markdown
## {Parameter name}
- **Value**: {exact value}
- **Rationale**: {why this value, or "Not specified in paper"}
- **Search range**: {if mentioned}
- **Sensitivity**: {low|medium|high — or "Not specified in paper"}
- **Source**: {section/table}
```

## src/execution/{module}.py  (when the work warrants it — grounded or absent)

Present only when the source provides **concrete code-shaped content**: actual repo code, or
explicit pseudocode/equations the paper prints. When a repo is provided, capture its real runnable
source files here in native form (transcribed) — not merely a stub of the novel mechanism; when only
pseudocode/equations exist, the reconstructed stub captures the **novel mechanism**. Either way it
must be grounded — never fabricated.

When the input is a run database / repo of many experiment runs, index them in a **run ledger at
`src/execution/artifacts.md`** — one entry per run (its id/label, status, and source link) — with each
experiment's `Run` field pointing at its entry. The final or successful runs are transcribed as
`src/execution/` files (the ledger links them); the failed, ablated, or dead-end runs are ledger
entries that link/ref the source-database location — never a fabricated per-run stub. Capturing only
the final/successful run is incomplete.

Every file declares its grounding on the first line:
```python
# Grounding: transcribed   — adapted from repo code; cite file:line in docstrings
# Grounding: reconstructed — from explicit paper pseudocode/equations; cite §/eq
```
Contents depend on the grounding:

**`transcribed` (a real repo file is provided)** — copy it faithfully in native form: full function
bodies, the file's own imports (third-party deps included), and its real scaffolding (CLI/argparse,
logging, entrypoints) all kept as in the repo. Do NOT replace working code with
`NotImplementedError`, strip plumbing, or reduce to signatures-only — that mutates the artifact and
breaks the cited `file:line`. Add only the `# Grounding` line and source-citing docstrings; otherwise
leave the file as it is in the repo.

**`reconstructed` (only pseudocode/equations exist)** — build a minimal stub of the novel mechanism:
- Typed function signatures using ONLY names/types the source states
- Docstrings that cite the source (`§4.2`, `Eq. 3`) — not paraphrases of this skill
- Implementation logic ONLY where the source provides it; everything unspecified stays
  `raise NotImplementedError("Not specified in paper")` — never plausible filler
- NO scaffolding (no argparse, logging, distributed wrappers); import only standard libraries + the
  field's core stack (torch/numpy, pandas/statsmodels, etc.)

Hard rule: do not invent API names, function bodies, constants, or hyperparameters. **If the paper
describes the method only in prose (no code, no printed pseudocode), do NOT write a `.py` stub or
pseudo-code — that information already lives in `logic/solution/`, and re-encoding it as code merely
duplicates it.** A concrete artifact that IS raw "code" — e.g. a prompt or template — is different:
store it verbatim in `src/prompts/`, don't paraphrase it. A hollow invented API is a hallucination.

## src/artifacts.md  (for non-code deliverables — NOT a substitute for capturing real source)

`src/` must still represent the implementation. When the deliverable is a released tool, library,
skill/specification, system, benchmark, or dataset rather than a code stub, describe the **real**
artifacts here — grounded in the actual repo/files when a repo is provided. One block per artifact:

**Exception — actual source code is captured, not pointed at.** When the repo contains real runnable
source files, copy those files into `src/execution/` in native form (`# Grounding: transcribed`,
cite path); do not reduce them to a prose block here. `artifacts.md` covers only deliverables with
no capturable source — released binaries, natural-language skill/spec docs, datasets referenced by
location. Naming a real `.py`/`.js`/… file here instead of capturing it is a coverage failure. For an
index of experiment **runs** (incl. failed/ablated/dead-end), use the run ledger
`src/execution/artifacts.md` instead of this file.

```markdown
## {Artifact name}
- **File(s) in repo**: {real path(s), verified to exist}
- **Nature**: {what it is — tool / library / skill spec / system / dataset}
- **What it does / contains**: {grounded description}
- **How to use / run**: {entry point, command, or interface}
- **Claims supported**: {C## ids}
```

Do not leave `src/` at just `environment.md` when the work clearly has an implementation (code,
configs, prompts, a released tool). Capture configs in `src/configs/`, prompts in `src/prompts/`,
and the rest here.

## data/  (when the work is data-driven)

- `data/dataset.md` — provenance, source, size, licensing, consent/IRB/ethics, variables
- `data/preprocessing.md` — cleaning, normalization, QC, feature construction

## src/environment.md  (mandatory core)

Reproducibility for any field. For purely analytical work, state so explicitly.

```markdown
# Environment
- **Language/runtime**: {Python version, R version, proof assistant, or "analytical — none"}
- **Framework**: {PyTorch/pandas/statsmodels/... version, etc.}
- **Hardware**: {GPU/CPU type, count, memory — or "n/a"}
- **Data sources**: {datasets/cohorts with access info — for data-driven work}
- **Key dependencies**: {list with versions}
- **Protocols**: {analysis protocol / preregistration / pipeline, if any}
- **Random seeds**: {if specified}
```

## evidence/proofs/{name}.md  (for theory/derivation work)

```markdown
# {Theorem/Lemma N}: {short title}
- **Source**: {Theorem N, Section X.Y}
- **Statement**: {formal statement}
- **Assumptions used**: {which assumptions from constraints.md}

## Proof
{proof sketch or full derivation}
```

---

## evidence/tables/{file}.md (+ screenshot)

Every numbered table gets BOTH this markdown file AND a screenshot `tableN.png` (the rendered
region of the source) saved beside it. Raw source-table transcription:

```markdown
# Table {N} - {Caption or short description}

**Source**: Table {N} in {paper/report title}
**Caption**: {verbatim or near-verbatim caption}
**Screenshot**: tableN.png
**Extraction type**: raw_table

| ... | ... |
| --- | --- |
| ... | ... |
```

Derived subset:

```markdown
# Derived subset - {Short description}

**Source**: Derived from Table {N} in {paper/report title}
**Caption**: {what part of the source table this subset preserves}
**Extraction type**: derived_subset
**Derived from**: `table{N}_{raw_file_name}.md`

| ... | ... |
| --- | --- |
| ... | ... |
```

Rules:
- Raw source-table files should reproduce the original row set relevant to that table, not a claim-specific slice
- If you drop rows, rename the file as a derived subset and declare the parent source
- Do not combine rows from multiple source tables while retaining a single original table number in the filename

---

## trace/exploration_tree.yaml

Each node should distinguish direct source support from reconstruction:

```yaml
tree:
  - id: N01
    type: question
    support_level: explicit | inferred
    source_refs: ["Table 2", "§4.1"]   # recommended for explicit nodes
    title: "{...}"
    description: "{...}"
```

Rules:
- `support_level: explicit` means the node is directly grounded in the provided source material
- `support_level: inferred` means the node is a reconstruction of the paper's logic, not a literal session record
- Explicit nodes should include `source_refs`
- Inferred nodes must not be presented as if they were directly observed historical events

---

## evidence/README.md

```markdown
# Evidence Index

## Tables
| File | Source | Claims | Description |
|------|--------|--------|-------------|
| [tables/{name}.md](tables/{name}.md) | Table N, §X.Y | C01, C02 | {one sentence} |

## Figures
| File | Source | Claims | Description |
|------|--------|--------|-------------|
| [figures/{name}.md](figures/{name}.md) | Figure N, §X.Y | C03 | {one sentence} |
```

## evidence/tables/{name}.md

ALL result tables, exact cell values:
```markdown
# Table N: {Title}
- **Source**: Table N, Section X.Y
- **Caption**: "{caption}"

| Column1 | Column2 | ... |
|---------|---------|-----|
| exact   | values  | ... |
```

## evidence/figures/{name}.md (+ screenshot)

ALL figures, read visually. Every numbered figure gets BOTH this markdown file AND a screenshot
`figureN.png` (the rendered region) saved beside it. Each file declares its type, extraction
method, and reading confidence so downstream layers know how trustworthy the contents are.

Shared header (all figure types):
```markdown
# Figure N: {Title}
- **Source**: Figure N, Section X.Y
- **Caption**: "{verbatim or near-verbatim caption}"
- **Screenshot**: figureN.png
- **Figure type**: {quantitative_plot | diagram | qualitative_sample | mixed}
- **Extraction method**: {exact_from_labels | digitized_estimate | visual_description}
- **Reading confidence**: {high | medium | low}
```

### quantitative_plot
Read values off the axes. Record axis scale — misreading a log axis corrupts every value.
```markdown
- **Plot kind**: {line | bar | scatter | box | histogram | heatmap}
- **Axes**: X = {label, units, scale: linear|log}, Y = {label, units, scale: linear|log}

| X | Y (Series A) | Y (Series B) | ... |
|---|-------------|-------------|-----|
| v | ≈v          | ≈v          | ... |

## Trend summary
{Directional reading that survives estimation error: monotonic/plateau/crossover at x≈..., variance bands, A vs B ordering.}
```
- Use exact values only when shown as data labels or stated in text; otherwise mark readings approximate with `≈` and set extraction method to `digitized_estimate`.
- A `quantitative_plot` file MUST contain a data table OR an explicit statement that points were unreadable (with `reading confidence: low`) plus a usable trend summary.

### diagram (architecture / pipeline / schematic)
Do NOT fabricate a data table. Capture structure, and mirror it into the relevant method/solution file.
```markdown
## Visual description
- **Components**: {boxes/modules with their labels}
- **Connections**: {arrows / data flow, source → target}
- **Annotations**: {shapes, colors, groupings that carry meaning}
- **What it conveys**: {the structural claim the diagram makes}
```

### qualitative_sample (example outputs, attention maps, failure cases)
```markdown
## Visual description
- **Shows**: {what the panel depicts}
- **Demonstrates**: {the qualitative point — e.g. failure mode, behavior, artifact}
- **Supports**: {claim ID(s) or gap ID(s) this is evidence for}
```

Rules:
- Mark every estimated numeric reading with `≈`.
- Never present a `digitized_estimate` as an exact source value.
- Never convert a `diagram` or `qualitative_sample` into a numeric table it does not contain.
- Subset/derived figure views follow the same `derived_`/`subset_` naming and provenance rules as tables.

---

## Appendix-sourced content

Appendix sections commonly carry worked examples, prompt templates, enumerated taxonomies,
annotation schemas, extended analyses, and prescriptive content. Route each into the ARA
layer where it best fits, preserving the granularity the source uses (for example, keep
per-entry descriptive fields for taxonomies rather than collapsing to names + frequencies).
The existing layer conventions above apply; create additional files only when no existing
file is a natural home.

---

## rubric/requirements.md (Only if rubric provided)

```markdown
# Rubric Requirements — {paper_id}

**Source**: PaperBench expert-authored reproduction rubric
**Total leaf requirements**: {N}

## {Category Group}

### R{NN}: {Short title}
- **Rubric ID**: {uuid}
- **Category**: {task_category} / {finegrained_task_category}
- **Weight**: {weight}
- **Requirement**: {verbatim from rubric}
- **ARA coverage**: {path to most specific ARA file, or "Not covered"}
- **Key detail**: {exact value from paper, or "Not specified in paper"}
```
