# Extension Harness

Run Claude agents on RE-Bench tasks **starting from the official reference solution**, with the goal of beating it. Two arms per task: `paper` (agent reads only the polished paper writeup) vs `ara` (agent reads the full ARA).

## Layout

```
code/extension-harness/
├── harness.py                  # Claude Agent SDK loop, token cap, JSONL trace
├── scoring/<task>/score.py     # stripped scorer (no METR group ceremony)
├── tasks/<task>/system_prompt.md
├── slurm/submit_<task>.sbatch  # one job per (task, arm, seed)
└── runs/                       # pointers / per-run YAML stubs
                                # (bulk artifacts on scratch)
```

Bulk run artifacts are written to scratch:
```
$SCRATCH_ROOT/extension-runs/<run_id>/
├── workdir/                    # what the agent sees: solution.py, score.sh, reference/
├── trace.jsonl                 # full message stream (one JSON per line)
├── solution_reference.py       # snapshot before agent edits
├── solution_final.py           # snapshot after agent stops
├── baseline_score.json         # score of the reference, before agent runs
├── final_score.json            # score of agent's final solution
└── metadata.json               # run config + token totals + cost
```

## Smoke test (one run, no SLURM)

Local-machine dry run with a tiny budget (no GPU, will fail at scoring but verifies the Agent SDK path works):

```bash
export ANTHROPIC_API_KEY=sk-...
.venv-extension-harness/bin/python code/extension-harness/harness.py \
    --task triton_cumsum --arm paper --seed 0 \
    --budget-tokens 50000 --model claude-sonnet-4-5 \
    --run-root /tmp/extension-runs --skip-baseline
```

## Real run (SLURM, H100)

```bash
export ANTHROPIC_API_KEY=sk-...
TASK=triton_cumsum ARM=paper SEED=0 BUDGET_TOKENS=500000 \
    sbatch code/extension-harness/slurm/submit_triton.sbatch
```

Override defaults via env vars: `TASK ARM SEED BUDGET_TOKENS MODEL SKIP_BASELINE`.

## Resume a crashed run

The Agent SDK exposes a `session_id` on the first `SystemMessage(subtype="init")`. To resume, find that ID in `trace.jsonl`:

```bash
jq -r 'select(.type=="system" and .subtype=="init") | .data.session_id' \
    $SCRATCH_ROOT/extension-runs/<run_id>/trace.jsonl
```

Then add `--resume <session_id>` to the harness call (planned; not yet wired into the CLI).

## Token budget

The harness accumulates `usage.input_tokens + usage.output_tokens` over every `AssistantMessage` and breaks the consumer loop when `>= --budget-tokens`. The agent then sees a clean shutdown; `metadata.json` records `halted_for_budget: true` and the actual token totals. (`max_budget_usd` is also set as a soft fallback.)

## Models

Default: `claude-sonnet-4-5`. Both arms use the same model for matched comparison.
