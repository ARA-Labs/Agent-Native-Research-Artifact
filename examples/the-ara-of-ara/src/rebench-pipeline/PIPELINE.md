# RE-Bench ARA Generation Pipeline

Meta-reference for converting RE-Bench task sources into clean, hallucination-free ARAs.
This document governs how all RE-Bench ARAs are built. It is **task-agnostic**; every
concrete number, file name, and score threshold lives in a per-task card under
`code/rebench-pipeline/tasks/<slug>.md`. Read this file + the relevant task card before
touching any artifact in `code/artifacts/rebench-*/`.

The `triton_cumsum` ARA (commit ecc15287) is the gold-standard reference for what the
output of this pipeline should look like end-to-end.

---

## 1. Source Locations (Path Patterns)

### Official task repos
```
/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/metr-re-bench/
  ai_rd_{slug}/
    README.md                  # starting + reference scores, human baselines, task instructions
    ai_rd_{slug}.py            # task family: EXACT scoring formula lives here
    requirements.txt           # environment constraints
    official_solution.zip      # password-protected; do NOT read directly

/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/official_solutions/
  ai_rd_{slug}/official_solution/
    {solution files}           # per-task — see task card
    notes.md                   # prose dev history (present for most tasks)
    score.log | score.txt      # final measured score for the official run (when present)
```
**Always read from `official_solutions/` — never from the zip directly.**

### MALT transcripts (Claude 4 Sonnet + Opus only, pre-filtered)
```
/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/malt_analysis/
  {slug}_new_models.jsonl      # ~12-22 runs per task; see task card for exact count
  # NOTE: optimize_llm_foundry has NO Claude 4 MALT data and is excluded from this pipeline.
```

### MALT JSONL structure
Each line is one run. Fields:
- `run_id`: unique run identifier.
- `model`: by default `claude-opus-4-20250514` or `claude-sonnet-4-20250514`. Per-task supplements may add other Claude variants (e.g. `claude-3-7-sonnet-20250219` for `rust_codecontests` — see its task card). The supplement file is a separate `*_supplement.jsonl`; the orchestrator iterates over both when Phase 2 spawns sub-agents for that task.
- `messages`: list of `{role, content}` — role is `user`, `assistant`, or `function`.
- Score submissions appear as `role=function` messages. **Content shape is task-specific and frequently non-trivial**:
  - Some tasks carry a dict (triton-style: `{'status': ..., 'score': <number>, 'message': {...}}`).
  - Some tasks carry a **JSON-serialized or Python-repr string** that must be parsed before indexing (`fix_embedding`).
  - Some tasks encode the raw metric under `message.{METRIC_NAME}` where `METRIC_NAME` is task-specific (`time`, `loss`, `loss_validation`, etc.).
  - Some tasks are **degenerate**: the raw metric IS the top-level `score`, with no separate key (`rust_codecontests`, `nanogpt_chat_rl`).
  - Some tasks are **score-hidden**: `score` is always `null` and no component is exposed (`small_scaling_law`).
  The task card documents the exact shape and keys for the relevant task; the Phase 2 extractor must consult it, not assume the triton form.
- Individual attempts = each time the agent calls the `score` action.

---

## 2. Scoring and the Beat-Reference Filter

Every RE-Bench task has three scores defined in its README: **starting**, **reference**
(official solution), and optionally a **best-human** baseline. The reference score defines
the beat-reference filter used to scrub MALT content (§3 rule 7).

### Direction matters

| Direction | Example tasks | "Beats reference" means | Filter action |
|-----------|---------------|-------------------------|---------------|
| Lower is better | `triton_cumsum`, `fix_embedding`, `restricted_mlm` | `score < reference` | Exclude the winning attempt node |
| Higher is better | `nanogpt_chat_rl`, `rust_codecontests`, `small_scaling_law` | `score > reference` | Exclude the winning attempt node |

For `small_scaling_law`, the scorer is `score = 1 - distance` (`ai_rd_small_scaling_law.py:179`), which is higher-better; the score is also hidden from the agent at runtime (`message` only returns `{is_valid, frac_flops_used}`), so the beat-reference filter is a no-op when processing MALT for that task. See `tasks/small_scaling_law.md` for the score-hidden extraction mode.

The filter applies **per-attempt, non-monotonically**: in a run with score sequence
1.5 → 0.8 → 0.3 → 0.6 → 1.1 against a lower-is-better reference of 0.47, include the
1.5 / 0.8 / 0.6 / 1.1 attempts as dead ends and exclude only the 0.3 attempt. Do not
stop reading at the first beat.

### Score formula source of truth

The formula lives in `metr-re-bench/ai_rd_{slug}/ai_rd_{slug}.py` — grep for `score`,
`log`, `loss`, or the return statement of the scorer. **Never infer the formula from
prose or from notes.md.** Transcribe it into the task card verbatim (e.g. `ln(time_ms)`
from `math.log(solution_time * 1000)`; `log(loss - 1.5)` from the task instructions).
Copy the formula into `logic/problem.md` of the ARA with a citation to the source line.

---

## 3. Hallucination Prevention Rules (task-agnostic)

1. **No invented numbers.** If a number is not in a MALT score message, the README, or
   the official solution source, it does not appear in the ARA. Use directional language
   for unsupported claims.

2. **No invented experiments.** Every entry in `logic/experiments.md` traces to a MALT
   score attempt, an official solution dev stage, or a task-family scorer definition.
   No hypothetical or planned-but-untested entries.

3. **No invented code.** `src/kernel/` contents are verbatim from the official solution
   directory. No paraphrases, no "cleanups".

4. **No fabricated exploration path.** Dev history comes from whatever the official
   solution actually shipped — a notebook (`triton_cumsum`, `small_scaling_law`), a
   `notes.md` narrative (`fix_embedding`, `restricted_mlm`, `nanogpt_chat_rl`,
   `rust_codecontests`), a shell orchestration script (`fix_embedding`), or a combination.
   Do not invent steps not visible in those artefacts. If a stage is mentioned only
   implicitly, tag its provenance `ai-suggested` and cite the source line.

5. **Score formula is whatever `ai_rd_{slug}.py` says.** Never assume `ln` vs `log10`,
   never invent direction. If the formula produces a counter-intuitive reference
   (e.g. `small_scaling_law` reference is numerically larger than starting), verify
   the sign convention in Phase 1 before building the ARA.

6. **`src/` schema**: `src/` = `kernel/` + `configs/` + `environment.md`. No
   `src/execution/` folder — the task scaffold (score.py, task_family.py) stays out of
   the ARA.

7. **Beat-reference filter is mandatory and enforced twice**: the sub-agent prompt states
   the filter (§5), and the Phase 3 merge performs a scrub that drops any attempt that
   still leaked through. Both enforcement points are required.

8. **Provenance on every node**: mark content as `source: official-solution` or
   `source: MALT (run_id={id}, model={model})`. No untagged content.

---

## 4. Layer Assignment Rules (task-agnostic)

### `logic/`
- `problem.md`: from README + `ai_rd_{slug}.py` task-family docstring. Math formulation
  is ground truth. Include exact scoring formula with source citation.
- `claims.md`: claims grounded in official solution code, task definition, or MALT
  evidence. Quantitative claims need an evidence ref; algorithmic claims are derivable
  from reading the source.
- `experiments.md`: each MALT score attempt = one experiment entry with
  `status: completed` and evidence refs. Official solution dev stages (§6) = experiment
  entries too. No planned-only entries in a shipped ARA.
- `solution/algorithm.md`: describes what the official solution *actually does*, read
  from the source files cited in the task card.
- `solution/heuristics.md`: from configs, autotune blocks, hyperparameter choices, and
  notes.md rationales. Every heuristic links to a specific line. If the rationale is
  not documented, tag `provenance: ai-suggested`.

### `src/`
- `src/kernel/`: verbatim files from the task card's "Solution artefacts" list.
- `src/configs/`: any config file from the official solution that is split out (per-stage
  training configs, autotune tables, hyperparameter YAMLs). Source = official-solution.
- `src/environment.md`: framework version, hardware, key dependencies from the
  task's `requirements.txt` plus README environment notes.

### `trace/`
- One `exploration_tree.yaml` with two provenance streams:
  - **Official solution stream**: dev stages drawn from whatever is available per task
    (notebook cells, notes.md paragraphs, script stages).
  - **MALT stream**: each run's individual attempts, grouped by `run_id` with model
    noted, filtered per §2.
- Node provenance field: `source: official-solution` or `source: MALT-run-{id}`.
- MALT dead ends: wrong output, timeout / OOM, compile error, API / infra failure.
  Tag infra failures distinctly from algorithmic failures — they carry different
  lessons (see `rust_codecontests` task card).

### `evidence/`
- `tables/human_baselines.md`: human runs from the README's baselines table.
- `tables/reference_scores.md`: starting + reference (+ best-human if present) from
  the README.
- `tables/malt_attempts.md`: all scored MALT attempts after the beat-reference scrub.
  Columns depend on task mode (see sub-agent prompt "Evidence table header" section):
  - Standard tasks: `run_id | model | attempt | approach | score ({FORMULA}) | {METRIC_NAME} | status`. Metric key per task: `time (ms)` for triton, `loss_validation` for fix_embedding (note: **not** `loss`; `loss` is a distractor key `loss_train`), `loss` for restricted_mlm.
  - Degenerate-metric tasks (`rust_codecontests`, `nanogpt_chat_rl`): collapse the metric column into a prose auxiliary (e.g. `n_successes/n_problems` or `win_vs_xl / win_vs_alpaca`); the `score` column carries the actual number.
  - Score-hidden tasks (`small_scaling_law`): drop the `score` column entirely; report `frac_flops_used` in its place.
- No other tables unless the pipeline actually ran a scorer.

---

## 5. MALT Extraction Workflow (Per Task)

### Reading protocol
Each run is read **sequentially and in full**, chunk by chunk. The sub-agent builds up a
running understanding of the trajectory: what the agent is reasoning about, what methods
it is designing, what it is learning between attempts. A bare score list loses the method
reasoning and failure lessons and is not acceptable output.

**Two rules that are always in the sub-agent prompt** (see `malt_extraction_agent_prompt.md`):

1. **🚫 NO TRUNCATION.** Never preview transcripts via `content[:N]` slices. The
   orchestrator dumps each chunk to a file; the sub-agent uses the Read tool with
   offset/limit pagination to consume each chunk in full. (See `ara/logic/solution/heuristics.md` H21.)

2. **🚫 NEVER SKIP CHUNKS.** Every chunk must be read end-to-end in order. MALT runs
   commonly place their most informative attempts (final submissions, post-feedback
   pivots) at the end; tail-skipping systematically biases the extraction. (See H22.)

### Sub-agent protocol
For each task, spawn one sub-agent per MALT run, **summed across every JSONL the task card
lists** (primary + any supplements). Per-task fan-out:

| Task | Primary | Supplement | Fan-out |
|------|---------|------------|---------|
| `triton_cumsum`, `restricted_mlm` | 22 | — | 22 |
| `small_scaling_law` | 21 | — | 21 |
| `fix_embedding` | 19 | — | 19 |
| `nanogpt_chat_rl` | 18 | — | 18 |
| `rust_codecontests` | 12 (Claude-4) | 10 (`claude-3-7-sonnet-20250219`) | 22 |

Each sub-agent receives:
1. The JSONL file path **for its assigned source** (primary or supplement) and run index.
2. The task card path (`code/rebench-pipeline/tasks/{slug}.md`) for score formula and
   reference threshold.
3. This `PIPELINE.md` for the reading + filtering rules.
4. The shared `malt_extraction_agent_prompt.md` template.

Sub-agent output (per run):
```json
{
  "run_id": "<id>",
  "model": "<claude-opus-4-20250514 | claude-sonnet-4-20250514 | claude-3-7-sonnet-20250219 (rust supplement only)>",
  "attempts": [
    {
      "attempt_number": 1,
      "approach_summary": "<one sentence>",
      "method_description": "<one paragraph, specific: libraries, configs, key decisions>",
      "score": <number | null>,
      "metric_value": <number | null>,   // time_ms, loss, win_rate, etc. — per task card
      "score_valid": true | false,
      "failure_mode": "<algorithmic | infra | dtype | timeout | ...>",
      "lesson": "<specific and transferable — 1-2 sentences>",
      "beats_reference": true | false,
      "include_in_ara": true | false
    }
  ],
  "run_summary": "<2-3 sentence arc across all attempts>",
  "dead_ends_extracted": ["<specific dead ends, each transferable>"],
  "arc_description": "<how the agent moved through the search space>"
}
```

### Aggregation (Phase 3 merge)
After all sub-agents complete:
1. Collect attempts with `include_in_ara: true` across all runs.
2. Deduplicate by approach — same method across multiple runs → one node with
   `runs_observed: N` and `models_affected: [list]`.
3. Group into: **dead ends** (wrong output, compile error, timeout, infra),
   **partial successes** (valid score but worse than reference).
4. Merge with the official solution stream (§6) into `trace/exploration_tree.yaml`
   under two top-level keys: `tree:` (official stream) and `malt_stream:` (MALT runs).
5. Populate `evidence/tables/malt_attempts.md` with every scored attempt surviving the filter.
6. **Scrub pass**: re-apply the beat-reference filter at the merge layer. Any attempt
   matching the beat condition that slipped through sub-agent classification is dropped
   here (see H23).

---

## 6. Official Solution Dev History Extraction

The extraction strategy adapts to what the official solution ships:

| Artefact available | Extraction strategy | Example task |
|--------------------|---------------------|--------------|
| Jupyter-style notebook (`*.py` with `# %%` cells or a dev notebook) | One stream node per cell boundary that represents a distinct approach | `triton_cumsum`, `small_scaling_law` |
| Multi-stage orchestration script (`*.sh`) + per-stage configs | One stream node per stage; config files are evidence | `fix_embedding` |
| `notes.md` prose with explicit milestones (loss values, named approaches) | One stream node per milestone; cite the `notes.md` line | `restricted_mlm` |
| Short `notes.md` with brief experiment log only | 3–5 stream nodes summarizing the visible arc; flag as sparse | `nanogpt_chat_rl`, `rust_codecontests` |

Each task card's "Dev-history stages visible in the source" section enumerates the
expected stream nodes for that task. Do not invent stages beyond what the card lists
without adding `provenance: ai-suggested` and a source citation.

---

## 7. Task Coverage Status

| Task | Official Artefacts | MALT Runs | Reference | Direction | ARA Built |
|------|-------------------|-----------|-----------|-----------|-----------|
| `triton_cumsum` | 3 .py | 22 (Opus 13 / Sonnet 9) | 0.47 | lower-better | ✅ (ecc15287) |
| `fix_embedding` | 5 .py + .sh + notes + score.log | 19 (Opus 10 / Sonnet 9) | 0.26 | lower-better | ⏳ next |
| `nanogpt_chat_rl` | 2 .py + notes + __init__ | 18 (Opus 12 / Sonnet 6) | 0.85 | higher-better | ⏳ |
| `restricted_mlm` | 5 .py + notes | 22 (Opus 11 / Sonnet 11) | 1.13 | lower-better | ⏳ |
| `rust_codecontests` | 3 .py + notes + score.log | 12 C4 (Opus 6 / Sonnet 6) + 10 claude-3-7-sonnet supplement | 0.13 | higher-better | ⏳ |
| `small_scaling_law` | notebook.py + answer.json + score.txt + 5 .png | 21 (Opus 9 / Sonnet 12) | 0.84 (README) / 0.5643 (score.txt, unreconciled) | higher-better (score-hidden) | ⏳ |
| `optimize_llm_foundry` | N/A | ❌ absent | — | — | skipped |

Notes:
- `small_scaling_law` is higher-better (`score = 1 - distance`, `ai_rd_small_scaling_law.py:179`) and score-hidden (`message` returns only `{is_valid, frac_flops_used}`). `score.txt` and README reference disagree — both are recorded in `evidence/tables/reference_scores.md` with their sources cited.
- `rust_codecontests` Claude-4 fan-out is unusually small (12 runs); the ARA supplements with 10 `claude-3-7-sonnet-20250219` runs that use the same `score()` scaffold (drop-in compatible). The supplement file is `malt_analysis/rust_codecontests_claude37_supplement.jsonl`. OpenAI-family models (o1-preview, o3) exist upstream for this task but use a different `submit_review` scaffold and are not ingested.

---

## 8. Invocation Order

For each task:
1. Read this file and the task card at `code/rebench-pipeline/tasks/{slug}.md`.
2. Follow `ORCHESTRATOR.md` Phases 0 → 4, substituting task-card values wherever a
   concrete score, file list, or run count is needed.
3. Commit the resulting `code/artifacts/rebench-{slug}/` ARA.
4. Update this file's §7 status row.
