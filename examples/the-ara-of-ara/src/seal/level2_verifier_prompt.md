# Level 2 Verifier Agent — Design Prompt

You are tasked with building the **ARA Seal Level 2 verifier**, an autonomous agent that audits the *epistemic integrity* of an Agent-Native Research Artifact (ARA). Read this entire document before writing code.

---

## 1. Background

An **ARA** is a typed, machine-traversable research artifact that replaces the traditional PDF paper. Its directory layout is:

```
PAPER.md                          # root manifest + layer index
logic/
  problem.md                      # observations → gaps → key insight
  claims.md                       # falsifiable assertions (C01, C02, ...)
  concepts.md                     # key technical terms
  experiments.md                  # declarative experiment plans (E01, E02, ...)
  solution/
    architecture.md
    algorithm.md
    constraints.md
    heuristics.md                 # H01, H02, ...
  related_work.md
src/                              # kernel code + configs + environment
trace/
  exploration_tree.yaml           # research DAG with typed nodes
                                  #   (question | experiment | dead_end |
                                  #    decision | pivot)
evidence/
  README.md                       # index
  results/                        # quantitative outputs
  logs/                           # execution traces
rubric/                           # (optional) PaperBench rubric mapping
```

**Claim schema** (each entry in `claims.md`):
```markdown
## C{NN}: {short title}
- **Statement**: {falsifiable assertion}
- **Status**: hypothesis | supported | refuted
- **Falsification criteria**: {what would disprove this}
- **Proof**: [{experiment IDs}]
- **Dependencies**: {other claim IDs or "none"}
- **Tags**: {keywords}
```

**Experiment schema** (each entry in `experiments.md`): must include `Verifies`, `Setup`, `Procedure`, `Metrics`, `Expected outcome`, `Baselines`, `Dependencies`.

**Exploration tree nodes** (`trace/exploration_tree.yaml`): `dead_end` nodes record approaches the authors tried and rejected, with a `failure_mode` and `lesson`. `pivot` nodes record course changes.

The full schema reference lives at `Agent-Native-Research-Artifact/skills/ingestor/references/ara-schema.md`.

---

## 2. Objective

Detect **epistemic defects** that survive structural (Level 1) checks. Level 1 has already verified schema conformance and cross-reference resolution for well-formed ARAs, but *some* structural issues in our evaluation corpus are specifically injected as symptoms of deeper logical defects (see §4). The Level 2 verifier must catch them on logical grounds — not merely by re-running Level 1 checks.

The verifier operates on the ARA **alone**, taking reported evidence at face value. It does not execute code and does not consult external sources.

It answers three questions per artifact:

1. **Claim–evidence entailment** — does each claim's cited evidence actually support it, given the claim's type (causal / generalization / improvement / scoping)?
2. **Scope and assumption audit** — does any claim's Statement reach beyond what its Falsification criteria, cited experiments, or declared assumptions can support?
3. **Narrative coherence** — does the claim set contradict the exploration tree, orphan evidence, or leave motivating questions unanswered?

---

## 3. Inputs and Outputs

### Input

A single argument: `artifact_dir: Path` — the root of an ARA directory (may be a clean ARA or an injected one).

Optional: `budget` (max LLM tokens), `model` (LLM identifier), `verbose` flag.

### Output

A JSON file `level2_report.json` written to the artifact root:

```json
{
  "artifact": "<paper name>",
  "artifact_dir": "<path>",
  "verifier_version": "<semver>",
  "model": "<llm id>",
  "passed": false,
  "num_findings": 7,
  "findings": [
    {
      "finding_id": "F01",
      "category": "claim_evidence_entailment | scope_audit | narrative_coherence",
      "defect_type": "fabricated_claim | missing_falsification | orphan_experiment | over_claim | rebutted_branch_leak | other",
      "severity": "blocker | major | minor",
      "target_file": "logic/claims.md",
      "target_entity": "C15",
      "evidence_span": "exact quoted text from the ARA that triggered the finding",
      "explanation": "1-3 sentences of plain-English reasoning",
      "suggested_fix": "1 sentence"
    }
  ],
  "per_category_counts": { ... },
  "token_usage": { "input": 0, "output": 0 }
}
```

Rules for the output:
- `defect_type` must be drawn from the closed vocabulary above (plus `other` for anything outside it).
- `target_entity` must be a real entity ID (`C01`, `E03`, `H02`, `N07`, ...) or `null`.
- `evidence_span` must be a *verbatim* substring of the ARA. The scoring harness will grep for it; paraphrases are treated as hallucinations.
- A finding with `severity == "blocker"` sets `passed = false`.
- If no defects are found, `findings = []`, `num_findings = 0`, `passed = true`.

### Per-run telemetry

Also append one line per finding to `level2_findings.jsonl` so multi-artifact runs are easy to concatenate and score.

---

## 4. The Defect Vocabulary (what the verifier is trained to see)

These are the five defect types used for evaluation (see `code/seal/inject_errors.py` and the per-artifact `injection_manifest.json` for exact ground truth):

| `defect_type` | Symptom in the ARA | Natural detection route |
|---|---|---|
| `fabricated_claim` | A claim's `Proof` cites an experiment ID that does not exist in `experiments.md`, and its Statement is not grounded anywhere else in the artifact. | Cross-reference `claims.md` → `experiments.md`; flag dangling refs; read the claim and check for any other anchor in the ARA. |
| `missing_falsification` | A claim is missing the `**Falsification criteria**` field. | Schema-style read of `claims.md`. |
| `orphan_experiment` | An experiment is declared but not referenced by any claim's `Proof`, and its `Verifies` points to a claim ID that does not exist. | Build the claim↔experiment bipartite graph; flag experiments with in-degree zero and dangling `Verifies`. |
| `over_claim` | A claim's Statement universalises scope ("all models / all datasets / all regimes") while its Falsification criteria and cited experiments cover only a narrow, concrete scope. | Compare Statement scope markers against Falsification criteria + `Verifies`'d experiment setup. |
| `rebutted_branch_leak` | A claim advocates an approach whose corresponding node in `trace/exploration_tree.yaml` is typed `dead_end` or `pivot` with a recorded `failure_mode`. | Match claim Statements against node titles / descriptions in the exploration tree; flag matches into rejected branches. |

The verifier is **not** restricted to these five types. It should report any logical defect it finds; the closed vocabulary above is how it tags the common cases so the scoring harness can compute per-type recall.

---

## 5. Required Behaviours

1. **Artifact-only.** Do not fetch external URLs, do not execute code, do not consult `evidence/results/*` as ground truth beyond what the claim itself references.
2. **Deterministic walk.** Always load `PAPER.md` first, then the full `logic/` layer, then `trace/exploration_tree.yaml`. Optionally sample `src/` and `evidence/README.md`. Record the read order in the report metadata for reproducibility.
3. **Explicit graph construction.** Build, in memory:
   - the claim dependency graph (from `Dependencies`),
   - the claim↔experiment bipartite graph (from `Proof` and `Verifies`),
   - the claim↔heuristic map (from `Code ref` / claim tags),
   - the typed exploration DAG.
   Run deterministic graph checks (dangling refs, orphans, cycles) *before* invoking any LLM reasoning.
4. **Type-aware entailment.** For each claim, infer its type (causal, generalization, improvement, scoping) from Statement cues, then check that the cited experiments match:
   - causal → requires isolating ablation,
   - generalization → requires heterogeneous test conditions,
   - improvement → requires a baseline with reported variance,
   - scoping → requires declared assumptions / bounds.
5. **Verbatim evidence.** Every finding must carry a quoted span from the ARA. If the verifier cannot quote, it must not report.
6. **Budget and cost.** Track input/output tokens. Short-circuit graph-only defects (`fabricated_claim`, `missing_falsification`, `orphan_experiment`) without LLM calls whenever possible; reserve LLM calls for `over_claim` and `rebutted_branch_leak`, which need semantic reasoning.
7. **Idempotence.** Running the verifier twice on the same artifact with the same model and seed must produce byte-identical `level2_report.json` (modulo timestamps, which go under a separate key).
8. **No false grounding.** The verifier may *not* assume a claim is supported just because prose in `problem.md` or `architecture.md` agrees with it; support must flow through `Proof` → `experiments.md` → `evidence/`.

---

## 6. Non-Goals

- Does not execute code (that is Level 3).
- Does not compare to external papers or benchmark against human reviews.
- Does not rate novelty, significance, or writing quality.
- Does not attempt to *repair* the ARA.

---

## 7. Interface

Expose a CLI entry point at `code/seal/level2_verifier.py`:

```
python code/seal/level2_verifier.py <artifact_dir> \
    [--model claude-opus-4-6] \
    [--budget 200000] \
    [--output <path>] \
    [--verbose]
```

And a Python API:

```python
from code.seal.level2_verifier import verify_level2, Level2Report

report: Level2Report = verify_level2(artifact_dir, model=..., budget=...)
```

A batch driver at `code/seal/run_level2.py` iterates over `code/artifacts_injected/*/` and `code/artifacts/*/` (the clean corpus serves as the false-positive control), writing per-artifact reports and an aggregate `code/seal/results/level2_summary.json`.

---

## 8. Evaluation Contract

The scoring harness (to be built next) will read:
- each injected artifact's `injection_manifest.json` (ground truth: 5 labeled defects per artifact),
- the verifier's `level2_report.json` (predictions).

It will compute:
- **Per-type recall:** fraction of ground-truth defects matched. A prediction matches a ground-truth defect iff `defect_type` agrees and either `target_entity` matches or `evidence_span` overlaps the injected `content_added` / `content_removed`.
- **False-positive rate on clean ARAs:** findings reported on the 23 untouched ARAs in `code/artifacts/`.
- **Agreement with PaperBench rubric failures** (stretch goal): map rubric leaf failures in `rubric/requirements.md` to Level-2-detectable categories and report precision/recall.
- **Cost:** tokens and wall-clock per artifact.

The verifier should therefore optimise for **high recall on the five injected defect types with low false-positive rate on clean ARAs.**

---

## 9. Deliverables

1. `code/seal/level2_verifier.py` — single-artifact verifier (graph checks + LLM reasoning).
2. `code/seal/run_level2.py` — batch driver over injected + clean corpora.
3. `code/seal/prompts/level2/*.txt` — LLM prompts for the semantic checks (one prompt per sub-task: entailment, scope audit, rebutted-branch matching).
4. `code/seal/results/level2_summary.json` — aggregated report.
5. A concise `code/seal/README_level2.md` describing the agent design, prompt strategy, and how to rerun.

Do not introduce new dependencies beyond what the repo already uses (`pyyaml`, `anthropic`, standard library). Reuse the parsing helpers in `code/seal/inject_errors.py` where appropriate (claim/experiment section parsing is already solved there).

---

## 10. Starting Context

- Injected corpus: `code/artifacts_injected/` (23 artifacts × 5 defects = 115 labeled defects).
- Clean corpus: `code/artifacts/` (23 PaperBench ARAs; false-positive control).
- Ground-truth manifests: `code/artifacts_injected/<paper>/injection_manifest.json`.
- Existing Level 1 validator: `code/seal/seal.py` (reuse its schema parsing if useful).
- ARA schema reference: `Agent-Native-Research-Artifact/skills/ingestor/references/ara-schema.md`.

Build the verifier against this contract. Keep the implementation tight: graph-first, LLM only where semantics are needed, and verbatim evidence on every finding.
