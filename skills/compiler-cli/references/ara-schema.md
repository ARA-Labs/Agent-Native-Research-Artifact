# ARA Directory Schema — Complete Field-Level Reference

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

Load the local [property-authoring contract](property-authoring.md) before claim capture,
revision, staging, or declaration authoring. It governs source fidelity, unsupported obligations,
neutral ARA-only views, and versioned check identity without adding core ARA fields.
Load this skill reference directly; knowledge access still uses `ara` under the boundary above.


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
src/                                # the CODEBASE (code in ANY language — never judged by a .py suffix)
  environment.md                    # ✓ Data/software/hardware/protocols/seeds
  artifacts.md                      # as warranted: pointer index to the codebase (every script/config/module)
  configs/                          # as warranted: hyperparameters / inference / deployment
  execution/{module}.{ext}          # as warranted: transcribed/grounded code, any language (or absent — see below)
  prompts/, ...                     # as warranted: prompt templates, etc.
data/                               # as warranted: dataset.md + preprocessing.md
trace/
  exploration_tree.yaml             # ✓ Research DAG: nested YAML tree with typed nodes
evidence/                           # derived + observed: diffs, run records, results, logs, tables, figures
  README.md                         # ✓ Index mapping every evidence file to claims
  tables/                           # ✓ every numbered Table: tableN.md + tableN.png
  figures/                          # ✓ every numbered Figure: figureN.md + figureN.png
  results/                          # as warranted: per-node run records (run tables: run_id, params, metrics, export_id)
  logs/                             # as warranted: log_pointers.md — direct per-run log pointers (by export_id)
  proofs/                           # as warranted: derivations / proofs
rubric/requirements.md              # (Only if a rubric is provided)
```

Every numbered table and figure in the source gets BOTH a markdown file and a screenshot `.png`
(see the evidence specs below). Additional files/subdirectories may be created on demand for
content that doesn't fit the standard layers (appendix worked examples, prompt templates,
taxonomies) — place such content where it best belongs.

## Progressive Disclosure (3 Levels)

- **Level 1 — PAPER.md** (~200 tokens): Frontmatter + layer index. Agent reads ONLY this through `ara show --document PAPER.md --source --full --json` to decide relevance.
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

Use the existing fields below. An unavailable value is an attributed unknown, not a reason to
invent support or crystallize a staged obligation:
```markdown
## C{NN}: {source-faithful title; a named method or bounded result is allowed}
- **Statement**: {verbatim source assertion, including exact variants, metrics, quantitative assertions, and every conjunct; identify a separately authored synthesis as interpretation}
- **Conditions**: {source scope, units, quantifier, aggregation, statistical unit, uncertainty commitment, and untested boundaries; attribute missing details}
- **Sources**: [{source revision/anchor and verbatim assertion; for each load-bearing number: `<value> ← <source ref> «verbatim line copied from source» [input|result]`, or `<value> ← [pending: reason]`; no unverified bare path}]
- **Status**: {hypothesis|supported|refuted; reflect actual support, not whether an executable declaration holds}
- **Falsification criteria**: {a concrete observation contradicting this assertion within its stated scope; for a bounded empirical comparison, reversal of a required ordering is meaningful; if undecidable from inputs, say why}
- **Proof**: [{real relevant experiment IDs: E01, E02; if none exist, use `pending` and state the missing-support reason in Evidence basis}]
- **Evidence basis**: {neutral evidence references and what they actually show, including conflicts, missing evidence, and unresolved meaning; candidates and check/repair answers belong in separately linked authoring records}
- **Dependencies**: {claim IDs a separate synthesis rests on, or claims this claim corrects/refines; not mere shared setup; omit when absent}
- **Tags**: {comma-separated keywords}
```

`Proof` IDs must resolve to real experiments in `experiments.md`; linked measurements must match
the assertion's exact methods, metrics, and scope. Missing proof is explicit. Do not create an
experiment just to populate `Proof`, or treat an absent variance estimate as zero.

Follow [What must survive](property-authoring.md#what-must-survive) and
[Author in this order](property-authoring.md#author-in-this-order). A quantitative source assertion
remains a first-class Statement. Keep any broader explanation in a separate synthesis with its own
identity and links to the preserved assertions. Neither a single result nor a component ranking
requires a mechanism inference. `Conditions` cannot repair an overclaim or replace missing conjuncts.

For example, the constructed source assertion "Fixed-A beats Base in average accuracy on both
Task-1 and Task-2, and uses less memory on both tasks." is an allowed Statement. Preserve
Fixed-A, Base, average accuracy, both tasks, and the memory conjunct even if the supplied evidence
contradicts part of it. Final accuracy or an adaptive variant is not a substitute. A separate
assertion of significant latency improvement retains that commitment; absent latency evidence or
variance is an explicit unsupported reason, not permission to invent a significance test.

An assertion with no faithful catalog mapping or no evidence stays in the contract's
all-selected-assertions ledger, even if absent from `aratest/spec.yaml`. Before crystallization,
use existing staged observation `content`/`context` and neutral evidence links. Compilation need
not turn every obligation into a settled claim or an empty executable property.

Keep neutral quotations, headers, and evidence semantics separate from authoring answers so the
contract's [isolated ARA-only view](property-authoring.md#isolated-ara-only-extraction) can retain
the full assertion without leaking candidates, selected operands, review feedback, or check history.
Apply [revisions and check identity](property-authoring.md#revisions-and-check-identity) to changed
obligations and declarations; old checks remain tied to old inputs, not the new snapshot.

---

## logic/concepts.md

Target ≥5 concepts, but capture only the paper's genuine technical terms. If fewer exist, record
the shortfall; never pad with trivial or borrowed terms (Rule 15). One section per concept:
```markdown
## {Term Name}
- **Notation**: {LaTeX or symbolic notation, or "—" if none}
- **Definition**: {Formal definition}
- **Boundary conditions**: {When it applies/not — or "Not specified in paper"}
- **Related concepts**: {other concept names}
```

---

## logic/experiments.md

Aim for ≥3 experiments only when the source actually describes them; record fewer or none with a
reason rather than inventing proof. These are declarative plans, NOT scripts or numerical result
tables. Source-grounded quantitative assertions remain in claims; measured results live in evidence.
Experiments and claims are **many-to-many**: list every real relevant experiment in `Proof`, without
forcing a 1:1 claim↔experiment ledger.

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
  - {source-faithful expectation; preserve any quantitative assertion or target in the linked claim}
  - {link measured results in evidence/ rather than copying a result table here}
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

Capture here is the **fallback, not the default**: transcribe code into `src/execution/` only when it
would otherwise be **lost** — it exists solely inside the paper, or its source is not externally
persisted. When the work's code/runs **persist in a linkable external store** (a repo, a run
database), do NOT copy them here — index them comprehensively in `src/artifacts.md` (see below). When
capture IS the call: actual repo code → capture real runnable files in native form (transcribed); only
pseudocode/equations the paper prints → a reconstructed stub of the **novel mechanism**. Either way it
must be grounded — never fabricated.

When the input is a run database / repo of many experiment runs, index it **comprehensively** in
`src/artifacts.md`: a link for **every** run and artifact (the per-run logs — e.g. a `runs.jsonl`
already indexes each — plus every config, candidate, log, and script), nothing aggregated into a vague
bucket and nothing copied. Each experiment's `Run` field points at the relevant entries. A lossy
subset — only the winning run, or runs collapsed into a single directory link — is the failure.

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

## src/artifacts.md  (the CODEBASE pointer index — code only, any language)

`src/artifacts.md` is the **pointer index to the experiment's codebase** — the *code*: every script,
config, and module, in **any language** (judged by content, never by a `.py` suffix). When the codebase
persists in a linkable store (a directory of script variants, a released/versioned repo), point at every
code artifact, grounded in the real files, nothing aggregated into a vague bucket and nothing copied.
**Run records do NOT belong here** — per-run logs, metrics, and run tables are evidence
(`evidence/results/`, `evidence/logs/log_pointers.md`), linked straight from trace/claims, not indexed in
`artifacts.md`. One block (or row) per **code** artifact:

**Capture is the fallback, not the default.** Transcribe a file into `src/execution/` only when it
would otherwise be **lost** — code that lives solely inside the paper, or a source not externally
persisted. When the source persists and is linkable, point to it here; copying a lossy subset (only
the winner, or files collapsed into a single directory link) is the failure.

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

## evidence/results/{node-or-name}.md  (run records — the outputs of running the code)

Per-experiment **run records**: the run table(s) a node produced. **This is where runs live**, not in
`src/artifacts.md`. One file per experiment node (or per result group):

```markdown
# {Node/result}: {short description}
- **Trace node**: N22
- **Claim**: C04

| run_id | {params…} | metric | export_id |
|--------|-----------|--------|-----------|
| …      | …         | …      | …         |
```

## evidence/logs/log_pointers.md  (direct per-run log pointers)

A single index of **direct pointers to each run's log**, grouped by node — `<store>/<export_id>/<log>`
(e.g. `train.log`, or the field's equivalent). Pointer-resolution only; do not transcribe logs:

```markdown
## N22: WD sweep (C04)
- `data/train/00023-…/train.log`   — winning run
- packet: v1-008
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
- Preserve original headers and axis order, exact method variants, metric identities, units,
  aggregation, uncertainty annotations, and approximation markers under the shared contract.
  Conflicting headers or aliases remain unresolved; normalizing a spelling must not merge variants.

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
    # OPTIONAL enrichment (Research Visualizer; omit when absent):
    # thinking: "{verbatim agent deliberation — why it did/branched}"
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
- Preserve source series identities, panel/task scope, axis order, and uncertainty annotations.
  Absent variance is missing information, never a zero-valued uncertainty estimate.
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
file is a natural home. Knowledge creation uses ara document operations. An additional
knowledge path outside logic must first be explicitly registered as a safe relative `.md`
path in PAPER frontmatter `knowledge_paths` through `paper.edit`/initialization;
`rubric/requirements.md` is the fixed allowlisted case. This does not authorize direct
knowledge writes or limit source-supported content/granularity.

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
