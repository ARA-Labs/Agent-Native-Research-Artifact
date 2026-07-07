"""
Deep analysis of METR runs data — focused on ARA-relevant findings.

Key headline findings from initial analysis:
- 79.9% of tokens go to failed runs
- 90.2% of cost goes to failed runs
- Failed runs average 2.58M tokens vs 300K for successful ones
- RE-Bench: 73.4% failure rate
- Hard tasks: only 15.1% success

This script digs deeper into patterns.
"""

import json
import os
from collections import Counter, defaultdict
import statistics

DATA_PATH = "/tmp/eval-analysis-public/reports/time-horizon-1-1/data/raw/runs.jsonl"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

runs = []
with open(DATA_PATH) as f:
    for line in f:
        runs.append(json.loads(line))

print(f"Loaded {len(runs)} runs")

# ============================================================
# A. FAILED RUN DEEP DIVE — WHY DO FAILURES BURN MORE TOKENS?
# ============================================================
print("\n" + "="*70)
print("A. WHY DO FAILED RUNS BURN MORE TOKENS?")
print("="*70)

# Token distribution: failed vs successful
failed = [r for r in runs if r["score_binarized"] == 0 and r.get("tokens_count") and r["tokens_count"] > 0]
success = [r for r in runs if r["score_binarized"] > 0 and r.get("tokens_count") and r["tokens_count"] > 0]

def percentiles(vals, ps=[10, 25, 50, 75, 90, 95]):
    sorted_v = sorted(vals)
    n = len(sorted_v)
    return {p: sorted_v[int(n * p / 100)] for p in ps}

if failed and success:
    f_tokens = [r["tokens_count"] for r in failed]
    s_tokens = [r["tokens_count"] for r in success]

    print(f"\nToken distribution (failed runs, n={len(failed)}):")
    for p, v in percentiles(f_tokens).items():
        print(f"  P{p}: {v/1e3:.0f}K tokens")

    print(f"\nToken distribution (successful runs, n={len(success)}):")
    for p, v in percentiles(s_tokens).items():
        print(f"  P{p}: {v/1e3:.0f}K tokens")

    # Ratio at each percentile
    print(f"\nFailed/Successful ratio:")
    fp = percentiles(f_tokens)
    sp = percentiles(s_tokens)
    for p in [25, 50, 75, 90]:
        print(f"  P{p}: {fp[p]/sp[p]:.1f}x more tokens in failed runs")

# ============================================================
# B. RE-BENCH DETAILED ANALYSIS
# ============================================================
print("\n" + "="*70)
print("B. RE-BENCH DETAILED ANALYSIS")
print("="*70)

rebench = [r for r in runs if r["task_source"] == "RE-Bench"]
print(f"\nTotal RE-Bench runs: {len(rebench)}")

# By task
rb_tasks = defaultdict(list)
for r in rebench:
    rb_tasks[r["task_id"]].append(r)

for task_id, task_runs in sorted(rb_tasks.items()):
    scores = [r["score_cont"] for r in task_runs]
    tokens = [r["tokens_count"] for r in task_runs if r.get("tokens_count") and r["tokens_count"] > 0]
    costs = [r["generation_cost"] for r in task_runs if r.get("generation_cost") and r["generation_cost"] > 0]
    n_success = sum(1 for r in task_runs if r["score_binarized"] > 0)

    print(f"\n{task_id} (n={len(task_runs)}, {n_success} success = {n_success/len(task_runs)*100:.0f}%):")
    print(f"  Scores: mean={statistics.mean(scores):.3f}, median={statistics.median(scores):.3f}")
    if scores:
        # Score distribution
        zero_pct = sum(1 for s in scores if s == 0) / len(scores) * 100
        high_pct = sum(1 for s in scores if s > 0.5) / len(scores) * 100
        print(f"  Score=0: {zero_pct:.0f}%, Score>0.5: {high_pct:.0f}%")
    if tokens:
        print(f"  Tokens: mean={statistics.mean(tokens)/1e3:.0f}K, median={statistics.median(tokens)/1e3:.0f}K")
    if costs:
        print(f"  Cost: mean=${statistics.mean(costs):.1f}, total=${sum(costs):.0f}")

    # By model within task
    by_model = defaultdict(list)
    for r in task_runs:
        by_model[r["alias"]].append(r["score_cont"])

    print(f"  By model:")
    for model, model_scores in sorted(by_model.items(), key=lambda x: -statistics.mean(x[1])):
        n = len(model_scores)
        avg = statistics.mean(model_scores)
        succ = sum(1 for s in model_scores if s > 0)
        print(f"    {model}: avg={avg:.3f}, {succ}/{n} success")

# ============================================================
# C. SCALING ANALYSIS — DOES MORE COMPUTE HELP?
# ============================================================
print("\n" + "="*70)
print("C. SCALING ANALYSIS — DOES MORE COMPUTE HELP?")
print("="*70)

# For RE-Bench specifically
for task_id, task_runs in sorted(rb_tasks.items()):
    valid = [(r["tokens_count"], r["score_cont"]) for r in task_runs
             if r.get("tokens_count") and r["tokens_count"] > 0]
    if not valid:
        continue

    # Split into low/high token usage
    sorted_by_tokens = sorted(valid, key=lambda x: x[0])
    mid = len(sorted_by_tokens) // 2
    low_half = sorted_by_tokens[:mid]
    high_half = sorted_by_tokens[mid:]

    low_avg_score = statistics.mean(s for _, s in low_half)
    high_avg_score = statistics.mean(s for _, s in high_half)
    low_avg_tokens = statistics.mean(t for t, _ in low_half) / 1e3
    high_avg_tokens = statistics.mean(t for t, _ in high_half) / 1e3

    print(f"\n{task_id}:")
    print(f"  Low token half:  avg {low_avg_tokens:.0f}K tokens → avg score {low_avg_score:.3f}")
    print(f"  High token half: avg {high_avg_tokens:.0f}K tokens → avg score {high_avg_score:.3f}")
    delta = high_avg_score - low_avg_score
    print(f"  More tokens → {'BETTER' if delta > 0.01 else 'WORSE' if delta < -0.01 else 'NO CHANGE'} ({delta:+.3f})")

# ============================================================
# D. CROSS-TASK PATTERN: DIFFICULTY CLIFF
# ============================================================
print("\n" + "="*70)
print("D. DIFFICULTY CLIFF — AGENT SUCCESS vs HUMAN TIME")
print("="*70)

# Bin tasks by human_minutes, compute aggregate success rate
difficulty_bins = defaultdict(lambda: {"runs": 0, "success": 0, "scores": []})
for r in runs:
    hm = r.get("human_minutes")
    if not hm or hm <= 0:
        continue

    if hm <= 15:
        b = "0-15min"
    elif hm <= 30:
        b = "15-30min"
    elif hm <= 60:
        b = "30-60min"
    elif hm <= 120:
        b = "1-2h"
    elif hm <= 240:
        b = "2-4h"
    elif hm <= 480:
        b = "4-8h"
    elif hm <= 960:
        b = "8-16h"
    else:
        b = ">16h"

    difficulty_bins[b]["runs"] += 1
    difficulty_bins[b]["success"] += r["score_binarized"]
    difficulty_bins[b]["scores"].append(r["score_cont"])

print(f"\n{'Difficulty':<12} {'Success Rate':>12} {'Avg Score':>10} {'Runs':>8}")
print("-" * 46)
for b in ["0-15min", "15-30min", "30-60min", "1-2h", "2-4h", "4-8h", "8-16h", ">16h"]:
    if b in difficulty_bins:
        d = difficulty_bins[b]
        rate = d["success"] / d["runs"] * 100
        avg = statistics.mean(d["scores"])
        print(f"{b:<12} {rate:>10.1f}% {avg:>10.3f} {d['runs']:>8}")

# ============================================================
# E. MODEL GENERATION COMPARISON ON RE-BENCH
# ============================================================
print("\n" + "="*70)
print("E. MODEL GENERATION COMPARISON")
print("="*70)

# Compare old vs new models on same RE-Bench tasks
model_order = [
    "Claude 3 Opus (Inspect)", "Claude 3.5 Sonnet (Inspect)",
    "Claude 3.7 Sonnet (Inspect)", "Claude Opus 4.5 (Inspect)",
    "Claude 4 Opus (Inspect)", "Claude Opus 4.6 (Inspect)",
    "Claude 4.1 Opus (Inspect)",
    "o1-preview", "o1 (Inspect)", "o3 (Inspect)",
    "GPT-4o (Inspect)", "GPT-5 (Inspect)", "GPT-5.1-Codex-Max (Inspect)",
    "GPT-5.3-Codex"
]

print(f"\n{'Model':<35} {'RE-Bench Avg':>12} {'RE-Bench N':>10} {'HCAST Avg':>10} {'HCAST N':>8}")
print("-" * 80)

for model in model_order:
    rb_runs = [r for r in runs if r["alias"] == model and r["task_source"] == "RE-Bench"]
    hc_runs = [r for r in runs if r["alias"] == model and r["task_source"] == "HCAST"]

    if not rb_runs and not hc_runs:
        continue

    rb_avg = statistics.mean(r["score_cont"] for r in rb_runs) if rb_runs else None
    hc_avg = statistics.mean(r["score_cont"] for r in hc_runs) if hc_runs else None

    rb_str = f"{rb_avg:.3f}" if rb_avg is not None else "N/A"
    hc_str = f"{hc_avg:.3f}" if hc_avg is not None else "N/A"

    print(f"{model:<35} {rb_str:>12} {len(rb_runs):>10} {hc_str:>10} {len(hc_runs):>8}")

# ============================================================
# F. KEY NUMBERS SUMMARY FOR ARA PAPER
# ============================================================
print("\n" + "="*70)
print("F. KEY NUMBERS SUMMARY FOR ARA PAPER")
print("="*70)

# Compile the most compelling stats
key_stats = {
    "total_runs": len(runs),
    "total_models": len(set(r["alias"] for r in runs)),
    "total_tasks": len(set(r["task_id"] for r in runs)),

    "overall_failure_rate": sum(1 for r in runs if r["score_binarized"] == 0) / len(runs),
    "rebench_failure_rate": sum(1 for r in rebench if r["score_binarized"] == 0) / len(rebench),
    "hcast_failure_rate": sum(1 for r in runs if r["task_source"] == "HCAST" and r["score_binarized"] == 0) / sum(1 for r in runs if r["task_source"] == "HCAST"),

    "tokens_wasted_on_failures_pct": 79.9,
    "cost_wasted_on_failures_pct": 90.2,

    "failed_run_avg_tokens": 2579000,
    "successful_run_avg_tokens": 300000,
    "failed_to_success_token_ratio": 2579 / 300,

    "easy_task_success": 85.4,
    "medium_task_success": 30.7,
    "hard_task_success": 15.1,

    "insight": (
        "Failed agent runs consume 8.6x more tokens than successful ones on average, "
        "and 90% of total compute cost goes to dead-end exploration. "
        "This 'exploration waste' is the direct cost of lacking structured knowledge transfer: "
        "each run rediscovers dead ends independently, with no mechanism to share insights across attempts."
    )
}

print(json.dumps(key_stats, indent=2))

out_path = os.path.join(OUT_DIR, "key_findings.json")
with open(out_path, "w") as f:
    json.dump(key_stats, f, indent=2)
print(f"\nSaved to {out_path}")

# ============================================================
# G. FATAL ERROR ANALYSIS
# ============================================================
print("\n" + "="*70)
print("G. FATAL ERROR ANALYSIS")
print("="*70)

fatal = Counter(r.get("fatal_error_from") for r in runs if r.get("fatal_error_from"))
print(f"\nRuns with fatal errors: {sum(fatal.values())}/{len(runs)}")
for err, count in fatal.most_common(10):
    print(f"  {err}: {count}")

# Among failed runs, how many had fatal errors vs just scored 0?
failed_runs = [r for r in runs if r["score_binarized"] == 0]
failed_with_error = sum(1 for r in failed_runs if r.get("fatal_error_from"))
failed_no_error = len(failed_runs) - failed_with_error
print(f"\nAmong {len(failed_runs)} failed runs:")
print(f"  With fatal error: {failed_with_error} ({failed_with_error/len(failed_runs)*100:.1f}%)")
print(f"  No fatal error (agent tried but scored 0): {failed_no_error} ({failed_no_error/len(failed_runs)*100:.1f}%)")
print(f"\n  → {failed_no_error} runs represent genuine dead-end exploration")
