# Evidence Index

All empirical results supporting claims in `logic/claims.md`. The eval/harness code that produced these numbers now lives in this artifact's own `src/` (see `src/eval/`, `src/extension-harness/`); the raw result blobs referenced below (result JSONs, run logs, checkpoints) are large, regenerable outputs of that code and are not checked into this artifact — this index maps each dataset to the claims it grounds and the code path that reproduces it.

## Understanding Evaluation (Layer 1)

**Source**: `code/eval/results/understanding/understanding_eval_report.json`

| Dataset | ARA | Baseline | Delta | Grounds |
|---------|-----|----------|-------|---------|
| Cat A overall (n=300) | 95.6% | 80.8% | +14.8pp | C04, C16 |
| Cat A PaperBench (n=230) | 96.7% | 89.8% | +6.9pp | C04 |
| Cat A RE-Bench (n=70) | 92.1% | 51.4% | +40.7pp | C04 |
| Cat B detail recovery (n=115) | 92.6% | 67.8% | +24.8pp | C04, C12, C16 |
| Cat C failure knowledge (n=35) | 81.4% | 15.7% | +65.7pp | C06, C16 |
| **Overall (n=450)** | **93.7%** | **72.4%** | **+21.3pp** | C04, C16 |

Token efficiency: Cat A ARA uses 84.6K vs 88.5K BL per question; Cat B 183K vs 178K; Cat C 139.3K vs 58.0K (BL abandons early when information absent).

## Reproduction Evaluation (Layer 2)

**Source**: `code/eval/reproduction/results/`

Difficulty-weighted success rate across 15 PaperBench papers (10 subtasks each, 150 total; 1,743 rubric requirements). Weights: easy×1, medium×2, hard×3.

| Condition | Score | Grounds |
|-----------|-------|---------|
| ARA | 64.4% | C05, C16 |
| Baseline (PDF + GitHub) | 57.4% | C05 |

Per-difficulty: easy +4.9pp, medium +5.6pp, hard +8.5pp. ARA wins 8/15 papers, ties 5, baseline leads 2.

## Extension Evaluation (Layer 3)

**Source**: `code/eval/extension/results/` (Tier 3 from-scratch evaluation, frozen for paper)

RE-Bench tasks, comparing ARA (full trace layer) vs. baseline (polished summary, trace stripped). Lower is better for tasks marked *.

| Task | ARA | Baseline | Ref | Grounds |
|------|-----|----------|-----|---------|
| restricted_mlm* | 1.133 | 1.754 | 1.13 | C06 |
| fix_embedding* | 0.895 | 1.039 | 0.26 | C06 |
| nanogpt_chat_rl | 0.895 | 0.850 | 0.85 | C06 |
| triton_cumsum* | 0.331 | 0.361 | 0.47 | C06 |
| small_scaling_law | 0.644 | 0.806 | 0.84 | C06 |
| rust_codecontests | 0.649 | 0.600 | 0.13 | C06 |
| optimize_llm_foundry* | pending | pending | — | C06 |

ARA wins 5/6 completed tasks.

### Extension-from-Reference Evaluation (post-paper push, 2026-04-23/24)

A separate **extension-from-reference** protocol: the agent starts from the official reference solution and tries to *beat* it (rather than build from scratch). All sonnet-4-6 unless noted; lower is better for tasks marked *.

**Source**: `/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs/{run_id}/` (per-run trace.jsonl + final_score.json + workdir snapshot). Plot scripts under `code/extension-harness/analysis/plot_*.py`. Latest snapshot 2026-04-24:

| Task | ARA s0 | Paper s0 | Ref | Notes |
|------|--------|----------|-----|-------|
| rust_codecontests | **85/165** (0.515) | 68/165 (0.412) | ~21/165 (0.13) | ara via H12 hand-coded SOLUTIONS dict; paper re-discovered the strategy at t=397min and built 112-entry few_shots cache |
| nanogpt_chat_rl | **0.830** | 0.7432 | 0.85 | paper got resume help; both used Replicate Llama-3-8b judge tournaments |
| fix_embedding* | **0.2363** | 0.2506 | 0.26 | ara wins by 0.014 (5.6% relative); both used 3-phase adapter pipeline |
| restricted_mlm* (4-6) | 1.03 (crashed at 5h32m) / 1.84 (s1 baseline) | **0.69** | 1.13 | **PAPER WINS on 4-6**: ara s0 hit SDK 1MB buffer crash; ara s1 burned 8h on broken HybridConvAttn trainings, never beat baseline |
| restricted_mlm* (4-5) | **0.7332** | 1.021 | 1.13 | ara wins by 0.29 absolute on 4-5 (s1) — opposite of 4-6 result |
| triton_cumsum* (4-5) | **0.273** (s8) / 0.441 (s2) | 0.6314 (s8) / 0.6355 (s0 prior) | 0.65 | ara s8 found a real kernel-level breakthrough; paper plateaus at reference |

**Net**: ARA wins 4/5 on sonnet-4-6 (rust, nanogpt, fix_embed, triton); paper wins MLM on 4-6. ARA wins 5/5 on sonnet-4-5.

The MLM 4-6 reversal is driven by:
- Paper s0 4-6 (job 7079164) found a `ConvMLMDilated` architecture and reached 0.69
- ARA s0 4-6 (job 7079165) crashed at 5h32m due to SDK 1MB JSON buffer overflow
- ARA s1 4-6 (job 7829208) burned 8h on broken HybridConvAttn trainings, never beat baseline
- Resume of ARA s0 4-6 (job 8011216) is in progress with new `DilatedConvMLMWithBiBigrams` architecture (combining paper's dilated convs + bigrams never tried in 22 prior MALT runs)

The 4-5 numbers were collected with the original harness; the 4-6 numbers required several harness fixes shipped 2026-04-23/24:
- SDK `max_buffer_size=16MB` (was 1MB; killed mlm ara s0 mid-run)
- PreToolUse Bash hook rejecting `for i in {1..N>10}` mass-batch scoring loops (multiple triton agents OOM'd cgroup → SIGTERM CLI)
- Per-task score timeouts (triton 1200s/1800s, rust 7200s/10800s; was 300s default)
- Pushback ceiling 1000, triggers expanded to {end_turn, stop_sequence, max_tokens, pause_turn}

#### Code references (now this artifact's own `src/` layer)

| Component | Path |
|---|---|
| Harness (SDK loop, PreToolUse hook, scoring) | `src/extension-harness/harness.py` |
| Per-task scoring scripts | `src/extension-harness/scoring/{triton_cumsum,rust_codecontests,restricted_mlm,nanogpt_chat_rl,fix_embedding}/` |
| Per-task system prompts (paper / ara arms) | `src/extension-harness/tasks/{task}/system_prompt.md` |
| SLURM sbatch templates | `src/extension-harness/slurm/submit_{task}{,_resume,_score_only}.sbatch` |
| Plot scripts | `src/extension-harness/analysis/plot_{task}_{model}_{seed}.py` |
| Generated plots | `src/extension-harness/plots/*.png` |

## Information Gap Analysis

**Source**: `code/eval/results/info_gap_aggregate.json`

23 PaperBench papers, 8,921 rubric requirements classified as sufficient / partial / absent.

| Category | Requirements | Sufficient | Partial | Absent | Grounds |
|----------|-------------|-----------|---------|--------|---------|
| Code Development | 3,942 | 37.3% | 54.9% | 7.8% | C09, C11 |
| Code Execution | 4,355 | 50.5% | 47.9% | 1.6% | C09, C11 |
| Result Analysis | 624 | 60.6% | 36.9% | 2.6% | C09, C11 |
| **Overall** | **8,921** | **45.4%** | **50.2%** | **4.4%** | C09 |

Gap type distribution: missing hyperparameters 26.2%, vague descriptions 21.9%, cross-reference-only 13.4% (grounds C12).

## Exploration Tax Analysis

**Source**: `code/eval/malt_analysis/exploration_tax_findings.json`, `key_findings.json`

METR eval-analysis-public v1.1, 24,008 agent runs, 21 models, 228 tasks.

| Metric | Value | Grounds |
|--------|-------|---------|
| Token share on failed runs | 59.2% | C13 |
| Dollar cost share on failed runs | 90.2% | C13 |
| Token ratio failed:successful (median) | 113× | C14 |
| RE-Bench failure rate | 73.4% | C13 |
| Well-defined task failure rate | 0.7% | C13 |
