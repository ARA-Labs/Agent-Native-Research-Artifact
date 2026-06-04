# Domain Profiles — Adaptive Mandatory File Structures

The ARA mandatory file set is **not one fixed list**. It is a small **Universal Core** that every
research artifact shares, plus a **domain Profile** that swaps in the method/artifact files that
actually fit the field. A benchmarking study should not be forced to write `configs/training.md`;
a biomedical data-science paper should not be forced to write a model architecture file.

The compiler selects (or synthesizes) one profile per artifact, records it in `PAPER.md`
frontmatter, and the validator checks the Universal Core **plus** the active profile's files.

---

## 1. Universal Core (ALWAYS required, every profile)

These encode the epistemic skeleton and are domain-independent. They must exist and be non-trivial
regardless of profile:

| File | Purpose |
|------|---------|
| `PAPER.md` | Manifest + layer index; frontmatter declares `ara_profile` and `profile_manifest` |
| `logic/problem.md` | Observations → gaps → key insight → assumptions |
| `logic/claims.md` | Falsifiable claims with proof pointers (C-blocks) |
| `logic/concepts.md` | ≥5 formal definitions |
| `logic/experiments.md` | ≥3 declarative verification/analysis plans (NO exact numbers) |
| `logic/related_work.md` | Typed dependency graph (RW-blocks) |
| `logic/solution/constraints.md` | Boundary conditions, assumptions, limitations |
| `trace/exploration_tree.yaml` | Research DAG (≥8 nodes, dead_end + decision) |
| `evidence/README.md` | Index mapping every evidence file to claims |
| ≥1 evidence file | In `evidence/tables/`, `evidence/figures/`, or `evidence/proofs/` |
| `src/environment.md` | Reproducibility: data sources, software, hardware, protocols, seeds (may state "analytical — no computational environment" for theory) |

Notes:
- The `≥` counts above are **source-bounded targets, not quotas** — meet them from genuine source
  content, never by padding or inventing (Rule 14). An honest artifact with fewer beats a padded one.
- `logic/experiments.md` is a **verification plan**, not "model training" — it generalizes to any
  field's way of testing a claim (an eval run, a statistical test, a proof obligation, a user study).
- The Universal Core deliberately does NOT include `architecture.md`, `algorithm.md`,
  `configs/training.md`, or `configs/model.md`. Those belong to specific profiles.

---

## 2. The Profile layer (method + artifact files, profile-specific)

Each profile defines the contents of the **method layer** (`logic/solution/`) and the
**artifact layer** (`src/`, and optionally `data/`). Pick the one that matches what the research
actually *produces*.

### `ml-model` — training or building a model (the original default)
Use when the contribution is a trained model, architecture, or optimization method.
- `logic/solution/architecture.md` — component graph
- `logic/solution/algorithm.md` — math + pseudocode + complexity
- `logic/solution/heuristics.md` — convergence/training tricks
- `src/configs/training.md` — hyperparameters (value, rationale, sensitivity)
- `src/configs/model.md` — architecture configs
- `src/execution/{module}.py` — ≥1 stub of the novel contribution
- Evidence emphasis: benchmark tables, training/eval curves

### `ml-eval` — evaluation, benchmarking, prompting, agents, interpretability (NO training)
Use when the contribution is a measurement, benchmark, prompting/agent method, or analysis of an
existing model — nothing is trained.
- `logic/solution/method.md` — the eval/prompting/probing method
- `logic/solution/protocol.md` — datasets, metrics, scoring rules, decoding/sampling settings
- `logic/solution/heuristics.md` — practical gotchas (prompt sensitivity, contamination control)
- `src/configs/inference.md` — model versions/endpoints, decoding params, API/runtime settings
- `src/execution/{module}.py` — harness or prompt-pipeline stub (prompts may live in `src/prompts/`)
- Evidence emphasis: result tables, qualitative samples
- Explicitly NOT required: `configs/training.md`, `configs/model.md`, `algorithm.md`

### `data-science` — statistical / observational / biomedical data analysis
Use for cohort studies, omics, epidemiology, social-science data work, any analysis-of-data
contribution where no algorithmic/model development is the point.
- `logic/solution/study_design.md` — design, cohort/sample, inclusion/exclusion, variables, endpoints
- `logic/solution/analysis_plan.md` — statistical models, tests, corrections, sensitivity analyses
- `logic/solution/heuristics.md` — practical data caveats (confounders, batch effects, missingness)
- `data/dataset.md` — provenance, source, size, licensing, consent/IRB/ethics
- `data/preprocessing.md` — cleaning, normalization, QC, feature construction
- `src/execution/{module}.py` — analysis pipeline stub
- Evidence emphasis: result tables, figures (forest plots, KM curves, ROC, volcano plots)
- Explicitly NOT required: `architecture.md`, `algorithm.md`, `configs/training.md`, `configs/model.md`

### `theory` — formal / mathematical contributions
Use when the contribution is theorems, bounds, or formal analysis.
- `logic/solution/formalization.md` — definitions, notation, problem setup
- `logic/solution/results.md` — theorems, lemmas, propositions (statements)
- `logic/solution/proofs.md` — proof sketches or full proofs
- (`constraints.md` from the core carries the assumptions)
- `evidence/proofs/*.md` — derivations satisfy the "≥1 evidence file" requirement; tables/figures optional
- `src/execution/{module}.py` — ONLY if a numerical experiment/verification exists; otherwise omit and let `environment.md` state "analytical — no computational environment"
- Explicitly NOT required: any `src/configs/*`, `architecture.md`, code stub, tables, or figures

### `systems` — a system, tool, or infrastructure contribution
Use for systems/DB/compiler/distributed/HPC engineering contributions.
- `logic/solution/architecture.md` — system component graph
- `logic/solution/design.md` — design decisions and trade-offs
- `logic/solution/heuristics.md` — tuning/operational tricks
- `src/configs/deployment.md` — deployment/runtime configuration
- `src/execution/{module}.py` — core mechanism stub
- Evidence emphasis: throughput/latency/scaling tables and figures

### `generic` — fallback / interdisciplinary / does-not-fit
Use when no profile above fits, or the work straddles fields.
- `logic/solution/methods.md` — whatever the method actually is
- `logic/solution/heuristics.md` — optional
- `src/execution/{module}.py` if code exists; otherwise `src/artifacts.md` describing the non-code artifacts produced
- Fill what fits; for any layer that genuinely does not apply, write an explicit
  "Not applicable for this work — {reason}" rather than padding or omitting silently.

> Code stubs across all profiles are **conditional and grounded**: include `src/execution/*.py`
> only when the source has implementable content (repo code, paper pseudocode/equations, or a named
> interface), tag each file `# Grounding: transcribed|reconstructed|interface-only`, and never invent
> an API. A prose-only contribution gets no stub — drop it from `profile_manifest`. See SKILL.md
> Stage 3 and ara-schema.md.

---

## 3. Selecting a profile

1. **Explicit override wins.** If the user passes `--profile <name>` or `--domain <field>`, honor it.
2. **Otherwise infer** from the inputs using these signals:

| Signal in the source | Likely profile |
|----------------------|----------------|
| Training loop, optimizer, loss, learning-rate schedule, checkpoints | `ml-model` |
| Benchmark/leaderboard, eval harness, prompts, "we evaluate", API model versions, no training | `ml-eval` |
| Cohort, patients/samples, p-values, regression, survival/odds ratios, IRB, omics | `data-science` |
| Theorem/Lemma/Proof, bounds, "we prove", no experiments | `theory` |
| Throughput/latency/QPS, system architecture, deployment, benchmarks of a tool | `systems` |
| None clearly dominant, or cross-field | `generic` |

3. **When ambiguous, decide yourself.** Pick the closest-fitting profile (or `generic`) and
   proceed — this is the compiler's call, not the user's. Only surface the choice to the user if it
   is both genuinely undecidable and materially changes the artifact.
4. A work may be **multi-profile** (e.g. a paper that both trains a model and runs a clinical
   analysis). In that case pick the dominant profile as the base and add the extra files from the
   secondary profile to `profile_manifest`.

---

## 4. Synthesizing a custom profile

The starter profiles are not exhaustive — the compiler is open-ended. If a field's real outputs do
not match any profile (e.g. an HCI study with interview transcripts, a hardware tape-out, a wet-lab
protocol), **synthesize** one:
- Choose a short `ara_profile` name (e.g. `hci-qual`, `wetlab`).
- List the method-layer (`logic/solution/`) and artifact-layer files that match the field's actual
  deliverables, each with a one-line rationale.
- Still satisfy the entire Universal Core.
- Record the synthesized file list in `PAPER.md`'s `profile_manifest` so the validator knows what to check.

A synthesized profile is first-class: the validator treats `profile_manifest` as the source of truth
for which profile-specific files are mandatory.

---

## 5. Declaring the profile in PAPER.md

Frontmatter must declare both the profile name and the concrete file list it commits to:

```yaml
ara_profile: data-science            # one of the starter names, or a synthesized name
profile_manifest:                    # the profile-specific mandatory files (beyond the Universal Core)
  - logic/solution/study_design.md
  - logic/solution/analysis_plan.md
  - logic/solution/heuristics.md
  - data/dataset.md
  - data/preprocessing.md
  - src/execution/cohort_pipeline.py
```

The validator checks: Universal Core (always) + every path in `profile_manifest` (exists, non-empty,
and — for files whose format this guide or `ara-schema.md` specifies — field-conformant). Cross-layer
binding checks (e.g. heuristic `Code ref` → `src/execution/`) apply only when both linked layers are
present in the active profile.
