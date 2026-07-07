# RE-Bench ARA Orchestrator

**You are the orchestrator.** This document is your operating procedure for converting one
RE-Bench task into a complete ARA. Read this in full before touching any artifact.

---

## Phase 0: Orient

Before anything else, read:
1. `code/rebench-pipeline/PIPELINE.md` — task-agnostic RE-Bench rules (priority source)
2. `code/rebench-pipeline/tasks/{task}.md` — **the task card** for the specific task you are building. Contains the score formula, starting/reference scores, direction, solution-file list, dev-history stages, MALT run count, and known hazards. **All concrete numbers, filenames, and thresholds come from here, not from PIPELINE.md.**
3. `.agents/skills/ingestor/SKILL.md` — ARA format and schema
4. `.agents/skills/ingestor/references/ara-schema.md` — field-level format for every file

PIPELINE.md overrides the ingestor skill on any conflict. The task card overrides PIPELINE.md on any task-specific detail. Keep all three in context throughout.

`triton_cumsum` is the gold-standard reference output (commit ecc15287). When in doubt about what a given layer should look like, compare against `code/artifacts/rebench-triton_cumsum/`.

Identify the task you are building. Locate:
- Task README + instructions: `/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/metr-re-bench/ai_rd_{task}/README.md`
- Task family (scoring formula): `/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/metr-re-bench/ai_rd_{task}/ai_rd_{task}.py`
- **Official solution files** (pre-extracted, use these): `/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/official_solutions/ai_rd_{task}/official_solution/`
- MALT transcripts (primary): `/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/malt_analysis/{task}_new_models.jsonl`
- MALT transcripts (supplements, task-specific): the task card's "MALT transcripts" entries enumerate any supplementary JSONLs. Currently only `rust_codecontests` ships a supplement (`rust_codecontests_claude37_supplement.jsonl`, 10 `claude-3-7-sonnet-20250219` runs to thicken its 12-run Claude-4 primary). Phase 2 fans out across **all** listed JSONLs, not just the primary.
- Output artifact: `code/artifacts/rebench-{task}/`

**Never read from `official_solution.zip` directly** — always use the pre-extracted path above.

Create the output directory structure before writing any files:
```bash
mkdir -p code/artifacts/rebench-{task}/{logic/solution,src/{kernel,configs},trace,evidence/tables,evidence/figures}
```

---

## Phase 1: Build Initial ARA from Official Solution

Read ALL official sources before writing anything:

1. `.../metr-re-bench/ai_rd_{task}/README.md` — reference score, starting score, human baselines, instructions
2. `.../metr-re-bench/ai_rd_{task}/ai_rd_{task}.py` — scoring formula, exact task instructions
3. `.../official_solutions/ai_rd_{task}/official_solution/*` — all solution files (pre-extracted)

Read every file in the official_solution/ directory with the Read tool. Do not skip any.

### What to build in Phase 1 (official-solution provenance only)

Use the ingestor skill (`SKILL.md` + `ara-schema.md`) as the format reference for every
file — field names, YAML structure, markdown templates. PIPELINE.md governs RE-Bench-specific
content rules (what goes where, what to exclude, provenance tags). When they conflict,
PIPELINE.md wins on content; ingestor wins on format.


**`PAPER.md`**
- YAML frontmatter: title, task, venue=RE-Bench, domain, ara_version=2.0
- Layer Semantics table (mandatory per PIPELINE.md)
- Layer Index: accurate list of what exists so far — update this at end of each phase

**`logic/problem.md`**
- Mathematical formulation (exact, from task instructions)
- Scoring formula (exact, transcribed verbatim from `ai_rd_{task}.py` — **not** paraphrased; the task card's "Scoring" section records the formula, direction, and log base). Example formulas across RE-Bench: `math.log(solution_time * 1000)` (triton), `log(loss_validation - 1.5)` (fix_embedding), `1 - distance` with a two-term distance (small_scaling_law), `n_successes / n_problems` (rust_codecontests).
- Starting score, reference score, best human score (from README, transcribed verbatim)
- Hardware context (from README and `requirements.txt` — no assumption about GPU type unless the task card states it)
- Key challenge (derivable from problem structure; for compute-kernel tasks this is a parallelization challenge, for scaling-law tasks it is extrapolation under a sub-budget, etc.)

**`logic/claims.md`**
- Only claims grounded in official solution code or task definition
- Algorithmic claims (what the solution does) → status: supported, source: official-solution
- Timing claims → status: untested (we have not run it ourselves)

**`logic/experiments.md`**
- Official solution dev stages → `status: completed, source: official-solution`. The artefact that carries the dev history is task-specific (see the task card's "Dev-history stages visible in the source" section and PIPELINE.md §6): a Jupyter-style `.py` notebook (triton_cumsum's `tao_baselining_notebook.py`, small_scaling_law's `notebook.py`), a multi-stage `.sh` + per-stage configs (fix_embedding), or prose milestones in `notes.md` (restricted_mlm, nanogpt_chat_rl, rust_codecontests).
- No planned entries — everything here already happened. If a stage is explicitly "planned but not shipped" in notes.md (e.g. rust_codecontests' `repair` in `notes.md:22`), tag it `status: explored-not-shipped` with provenance on the exact source line, and do NOT count it as a completed experiment.

**`logic/solution/algorithm.md`**
- Describe what the official solution actually does — read the code, describe it in prose
- For triton_cumsum: the 3-kernel pipeline (prefix_odd_block → contitional_cumsum → add_block_sums)
- Do NOT describe a textbook algorithm that differs from what the code does

**`logic/solution/heuristics.md`**
- Extracted from autotune configs and code comments in official solution
- Every heuristic cites the specific line/file it came from
- If rationale is not in the code, mark `provenance: ai-suggested`

**`logic/solution/architecture.md`**, **`constraints.md`**, **`concepts.md`**, **`related_work.md`**
- Derive from official solution + task definition
- Mark anything inferential as `provenance: ai-suggested`

**`src/kernel/`**
- Copy official solution files verbatim — do not modify or paraphrase
- Source = official-solution

**`src/configs/autotune.md`**
- Extract exact values (BLOCK_SIZE, NUM_STAGES, num_warps, grid_size) from official code

**`src/environment.md`**
- Framework versions, hardware, key runtime dependencies read from the task's `requirements.txt` + README environment notes + `manifest.yaml` (when present). What matters per task varies: Triton + GPU for kernel tasks; PyTorch + GPU count + RAM for training tasks (e.g. `nanogpt_chat_rl` requires 2 × H100 + 200 GB per `manifest.yaml:10-14`); OpenAI API + Rust toolchain for `rust_codecontests`. Do not assume GPU dependency if the task card does not declare one.

**`trace/exploration_tree.yaml`**
- Seed with official solution dev history (from baselining notebook):
  - Root question node
  - Official solution stages as experiment/decision nodes
  - Any alternative approaches in the zip as dead_end nodes
  - All nodes: `provenance: official-solution`
- Node IDs: N01 onward

**`evidence/tables/human_baselines.md`**
- Human scores from README (exact values, no rounding, no inferred approaches)

**`evidence/tables/reference_scores.md`**
- Starting score, reference score — from README

**`evidence/README.md`**
- Index of all evidence files built so far

After Phase 1: verify the ARA is internally consistent. Every claim has a proof ref,
every experiment links to evidence, every heuristic cites a file. Fix gaps before Phase 2.

---

## Phase 2: MALT Sub-Agent Extraction

### Enumerate MALT sources for this task

The task card names the JSONL(s) to ingest. Every task has a primary Claude-4 JSONL at `{task}_new_models.jsonl`; some tasks (currently `rust_codecontests`) add a supplementary JSONL (e.g. `rust_codecontests_claude37_supplement.jsonl`). Read the task card's "MALT transcripts" entries and iterate Phase 2 over **every listed JSONL**.

```python
import json, os
jsonl_sources = [
    ("primary", f"/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/malt_analysis/{task}_new_models.jsonl"),
    # add supplements as listed in the task card:
    # ("supplement", f".../malt_analysis/{task}_claude37_supplement.jsonl"),
]
for label, jsonl in jsonl_sources:
    if not os.path.exists(jsonl):
        print(f"{label}: missing, skipping {jsonl}")
        continue
    with open(jsonl) as f:
        runs = [json.loads(l) for l in f]
    from collections import Counter
    print(f"{label}: {len(runs)} runs, models={Counter(r['model'] for r in runs)}")
```

### Assign node/experiment ID ranges before spawning
Check the highest node ID currently in `trace/exploration_tree.yaml`. Assign each sub-agent
a non-overlapping range of IDs so their outputs can be merged without collision:
- Sub-agent 0: N{current_max+1} to N{current_max+50}
- Sub-agent 1: N{current_max+51} to N{current_max+100}
- etc.

Allocate contiguous blocks across *all* JSONL sources so that supplement runs do not collide with primary runs.

### Spawn sub-agents in parallel
Spawn every (run_index, jsonl_source) combination simultaneously using the Agent tool with `run_in_background=True`.
Use the prompt template from `code/rebench-pipeline/malt_extraction_agent_prompt.md`,
filling in (the template requires all of these — the sub-agent will fail if any are omitted):

- `{JSONL_PATH}` — absolute path to the JSONL for this sub-agent's source
- `{RUN_INDEX}` — 0-based index into that JSONL
- `{TASK_SLUG}` — e.g. `rust_codecontests`
- `{TASK_CARD_PATH}` — `code/rebench-pipeline/tasks/{TASK_SLUG}.md`
- `{REFERENCE_SCORE}`, `{SCORE_DIRECTION}`, `{SCORE_FORMULA}`, `{METRIC_NAME}`, `{METRIC_UNIT}` — copy directly from the task card's Scoring section. For score-hidden tasks (`small_scaling_law`) set `{METRIC_NAME}` to the auxiliary field named by the card (e.g. `frac_flops_used`) and leave `{SCORE_FORMULA}` blank; the card's extraction mode handles the rest.
- `{NODE_ID_START}`, `{EXP_ID_START}` — assigned range above
- `{OUTPUT_DIR}`: `code/rebench-pipeline/malt_outputs/{task}/{source_label}_run_{run_id}/` where `source_label` is `primary` or the supplement name. Source-labeling the directory prevents primary/supplement collisions when the orchestrator merges.

You will be notified as each sub-agent completes. Do NOT wait for all — merge results
as they arrive.

---

## Phase 3: Continuous Merge (as sub-agents complete)

When a sub-agent completes, immediately:

1. **Read** its output files:
   - `run_summary.yaml` — understand what the run contributed
   - `trace_nodes.yaml` — new nodes to add to exploration tree
   - `evidence_rows.md` — rows to append to `evidence/tables/malt_attempts.md`
   - `insights.yaml` — potential heuristic/claim updates

2. **Deduplicate** trace nodes against what already exists:
   - Same failure pattern already in tree? → increment `runs_observed` on existing node, add model to `models_affected`
   - Genuinely new approach? → append as new node

3. **Update `trace/exploration_tree.yaml`** — append new nodes under appropriate parent.
   Never remove or edit existing nodes.

4. **Update `evidence/tables/malt_attempts.md`** — append new rows. Create file if first run.

5. **Update `logic/experiments.md`** — if sub-agent found a new experiment pattern not
   already listed, add a new E-entry (status: completed, source: MALT).

6. **Update `logic/claims.md`** — if insights support or refute an existing claim, update
   its Proof field and status. If a new claim is warranted, add it.

7. **Update `logic/solution/heuristics.md`** — if insights reveal a new heuristic (e.g.
   a specific API limitation confirmed across multiple runs), add it.

8. **Update `PAPER.md` Layer Index** — reflect any new files created during merge.

After each merge, verify cross-layer consistency:
- New evidence rows have corresponding experiment entries
- New claims have proof refs
- New heuristics cite source runs

---

## Phase 4: Final Consistency Pass

After all sub-agents complete and all merges are done:

1. Read the full `trace/exploration_tree.yaml` — check for duplicate approaches, gaps in narrative
2. Read `logic/claims.md` — verify every claim's proof refs still resolve
3. Read `evidence/README.md` — update index with any new tables added during Phase 3
4. Update `PAPER.md` Layer Index with final file counts
5. Run a quick mental Seal check:
   - All mandatory files exist and are non-empty?
   - No `log10` in scoring context?
   - No invented timing numbers?
   - All MALT content has `source: MALT run_id=X` provenance?
   - All official solution content has `source: official-solution` provenance?

---

## Invariants (never violate)

- **Append-only trace**: never edit or remove existing nodes in exploration_tree.yaml
- **Evidence-only numbers**: exact scores/times live in evidence/ only, not in logic/
- **No src/ from MALT**: src/kernel/ is official solution only
- **Provenance on everything**: every node, claim, heuristic carries its source
- **PIPELINE.md over ingestor**: on any conflict, PIPELINE.md wins
- **No invented content**: if a source is ambiguous, note the ambiguity; do not fill gaps
