# Extension-Harness Progress Log

Last updated: 2026-04-20

Three RE-Bench extension tasks. Two arms: **paper** (PDF only) vs **ara**
(Agent-Native Research Artifact). Comparing whether ARA changes agent behavior.

## triton_cumsum (sonnet-4.5)

Goal: improve a Triton conditional-prefix-sum kernel. Score = log(solution_ms /
torch_ms), lower is better. Per-hardware baseline ~0.65 on H100 (from
`baseline_score.json` in each run dir).

### Completed / live runs

| run                      | job        | n_scores | best  | end_min | notes |
|--------------------------|------------|----------|-------|---------|-------|
| paper s0                 | 6754693    | 31       | 0.638 | 104     | finished, devolved into background `for i in {1..1000}; do bash score.sh &; done` after plateau |
| paper s2                 | 6848031    | 29       | 0.630 | 48      | FAILED (exit 1) at 48 min |
| ara   s0                 | 6754694    | 76       | 0.246 | 202     | FAILED (exit 1) at 3h22m |
| ara   s2                 | 6848032    | 48       | 0.436 | 213+    | LIVE (final_score phase) |

Trend across N=2 each: paper plateaus right at baseline; ara breaks far below.
Plot: `plots/triton_45_live_paper_s0_ara_s2.png`.

### Why paper s0 failed (Phase analysis from trace)

- 0–30 min: real solution edits (`solution_compile.py`, `solution_pinned.py`,
  autotune variants) → best 0.638 by 12 min.
- 30–80 min: hit ceiling, started chaining `bash score.sh && bash score.sh`
  for noise.
- 80–104 min: explicit anti-pattern violation:
  - `while true; do timeout 25 bash score.sh; done`
  - `for i in {1..1000}; do (timeout 25 bash score.sh &); done`
  - Self-status: "20,000+ scoring runs / 15k+ parallel jobs active".
- SDK ended at 104 min (not full 8h SLURM wall) — likely GPU thrash.

Hypothesis: PDF gives the recipe but no exploration map; once first tweaks
hit baseline, agent has no directions left and tries to "use the budget" via
parallel scoring. ARA's exploration tree (live branches: stream-K, warp
specialization; known dead ends) keeps it productive.

### In-flight (queued 2026-04-20)

To strengthen N: 2 new sonnet-4.5 seeds, kempner_h100, 8h wall:

| job      | arm    | seed |
|----------|--------|------|
| 6938976  | paper  | 3    |
| 6938978  | ara    | 3    |

After completion, extend `analysis/plot_triton_sonnet45_s0_s2.py` to a
multi-seed bar/box plot of best-score and survival curves.

### Stale (sonnet-4.6 batch — different model, separate analysis)

paper s8 (6772400), ara s0 (6776923), ara s88 (6772401). Plot:
`plots/triton_best_so_far_paper_s8_ara_s0.png`,
`plots/triton_4.6_live.png`.

### Failed resume

paper s0 resume attempt (6897265): SIGKILL at t=45m turn 40 even after
mem bump 100G→200G. Options: bump to 400G; abandon resume + cherry-pick
solution_best.py into a fresh run; accept 6848031's pre-death scores.

## restricted_mlm (sonnet-4.6)

Best known: ara s1 — 50 score attempts, best loss 0.733 (recorded as
`workdir/score_*.json`, not in scores.jsonl). All 3 paper runs to date have
0 valid scores (training jobs got SIGTERM/SIGKILL during pretrain).

In-flight: paper s1 (6858168) — running, 0 scores yet.

To do:
- paper s0 fresh submit
- ara s0 fix (truncated checkpoint)
- ara s1 has best scores but no `final_score.json` — re-score it from
  the checkpoint to get a clean number for the table.

## nanogpt_chat_rl (sonnet-4.5)

Setup committed (a95f1915). Validated end-to-end at 1/8 scale (timing_probe
mode): setup 152s, step 0 226s, step 1 202s, score 33s, total 595s. Win rate
0.7656 after 2 steps (reference is 0.85 after full 4). Full-scale extrapolation:
~2h training, well under 8h wall.

Patches applied:
- `scoring/nanogpt_chat_rl/rl_finetune_starter.py`: guard `torch.compile`
  (Dynamo not supported on Python 3.12+).
- `harness.py`: `NANOGPT_SPEC` with `needs_replicate_key`, replicate key
  handling in `setup_workdir` + `main_async`, cli_stderr capture.

Blocker: Replicate credit < $20 → 600/min rate limit, 50 burst. Smoke
completed via async retries but agent runs would throttle. **Top up
Replicate credit above $20 before launching real agent runs.**

## Cross-cutting future work

1. **Most important:** finish triton paper-vs-ara N=4 comparison. If the
   trend holds, this is a clean ARA vs PDF result with a non-trivial gap
   (~0.4 best-score difference, ~3x speedup ratio).
2. Restore restricted_mlm paper coverage (currently 0/3 runs produced
   scored attempts).
3. Top-up Replicate credit, then run nanogpt_chat_rl paper×ara × 2 seeds.
4. Re-score MLM ara s1 checkpoint to get clean final_score.json.
5. Decide on triton paper s0 resume strategy (400G vs cherry-pick vs
   accept).

## Reference files

- harness: `code/extension-harness/harness.py`
- task specs: `code/extension-harness/tasks/{triton_cumsum,restricted_mlm,nanogpt_chat_rl}/`
- scoring: `code/extension-harness/scoring/<task>/`
- run artifacts: `/n/netscratch/sompolinsky_lab/Everyone/zechenzhang/ara-project/extension-runs/<run_id>/`
- plots: `code/extension-harness/plots/`
- analysis: `code/extension-harness/analysis/`
- slurm submission: `code/extension-harness/slurm/submit_<task>.sbatch`
