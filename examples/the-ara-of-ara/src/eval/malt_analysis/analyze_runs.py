"""
Analyze METR eval-analysis-public runs.jsonl for ARA paper insights.

Focus areas:
1. Exploration patterns: action counts, token usage, cost vs score
2. Failure rates: what fraction of runs achieve zero score
3. RE-Bench vs HCAST comparison
4. Model scaling: how does performance change with more resources
5. Dead-end quantification: runs that consumed resources but scored 0
"""

import json
import os
from collections import Counter, defaultdict
import statistics

DATA_PATH = "/tmp/eval-analysis-public/reports/time-horizon-1-1/data/raw/runs.jsonl"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load all runs
print("Loading runs.jsonl...")
runs = []
with open(DATA_PATH) as f:
    for line in f:
        runs.append(json.loads(line))

print(f"Total runs: {len(runs)}")

# ============================================================
# 1. BASIC STATS
# ============================================================
print("\n" + "="*60)
print("1. BASIC STATS")
print("="*60)

task_sources = Counter(r["task_source"] for r in runs)
print(f"\nBy task source: {dict(task_sources)}")

models = Counter(r["alias"] for r in runs)
print(f"\nModels ({len(models)} unique):")
for m, c in models.most_common(15):
    print(f"  {m}: {c} runs")

task_families = Counter(r["task_family"] for r in runs)
print(f"\nTask families ({len(task_families)} unique):")
for tf, c in task_families.most_common(15):
    print(f"  {tf}: {c} runs")

# ============================================================
# 2. FAILURE RATE ANALYSIS (key for ARA)
# ============================================================
print("\n" + "="*60)
print("2. FAILURE RATE ANALYSIS")
print("="*60)

total = len(runs)
zero_score = sum(1 for r in runs if r["score_binarized"] == 0)
nonzero_score = total - zero_score
print(f"\nOverall: {zero_score}/{total} runs scored 0 ({zero_score/total*100:.1f}%)")
print(f"         {nonzero_score}/{total} runs scored >0 ({nonzero_score/total*100:.1f}%)")

# By task source
for source in ["HCAST", "RE-Bench", "SWAA"]:
    src_runs = [r for r in runs if r["task_source"] == source]
    if not src_runs:
        continue
    src_zero = sum(1 for r in src_runs if r["score_binarized"] == 0)
    print(f"\n{source}: {src_zero}/{len(src_runs)} failed ({src_zero/len(src_runs)*100:.1f}%)")

# By model (top models only)
print("\nFailure rate by model:")
for model in ["Claude Opus 4.5 (Inspect)", "Claude Opus 4.6 (Inspect)",
              "Claude Sonnet 4.6 (Inspect)", "o3 (Inspect)", "o1 (Inspect)",
              "GPT-4o (Inspect)", "Claude 3.5 Sonnet (Inspect)", "Claude 3 Opus (Inspect)"]:
    model_runs = [r for r in runs if r["alias"] == model]
    if not model_runs:
        continue
    m_zero = sum(1 for r in model_runs if r["score_binarized"] == 0)
    m_total = len(model_runs)
    avg_score = statistics.mean(r["score_cont"] for r in model_runs)
    print(f"  {model}: {m_zero}/{m_total} failed ({m_zero/m_total*100:.1f}%), avg_score={avg_score:.3f}")

# ============================================================
# 3. WASTED EFFORT / DEAD-END ANALYSIS
# ============================================================
print("\n" + "="*60)
print("3. WASTED EFFORT / DEAD-END ANALYSIS")
print("="*60)

# How many tokens/dollars were spent on runs that scored 0?
zero_runs = [r for r in runs if r["score_binarized"] == 0]
nonzero_runs = [r for r in runs if r["score_binarized"] > 0]

def safe_sum(vals):
    return sum(v for v in vals if v is not None and v == v)  # filter NaN

zero_tokens = safe_sum(r.get("tokens_count", 0) for r in zero_runs)
total_tokens = safe_sum(r.get("tokens_count", 0) for r in runs)
zero_cost = safe_sum(r.get("generation_cost", 0) for r in zero_runs)
total_cost = safe_sum(r.get("generation_cost", 0) for r in runs)

print(f"\nTokens spent on failed runs: {zero_tokens/1e6:.1f}M / {total_tokens/1e6:.1f}M total ({zero_tokens/total_tokens*100:.1f}%)")
print(f"Cost on failed runs: ${zero_cost:.0f} / ${total_cost:.0f} total ({zero_cost/total_cost*100:.1f}%)" if total_cost > 0 else "Cost data not available")

# Average tokens per run: failed vs successful
if zero_runs:
    avg_tokens_zero = safe_sum(r.get("tokens_count", 0) for r in zero_runs) / len(zero_runs)
    avg_tokens_nonzero = safe_sum(r.get("tokens_count", 0) for r in nonzero_runs) / len(nonzero_runs) if nonzero_runs else 0
    print(f"\nAvg tokens per failed run: {avg_tokens_zero/1e3:.1f}K")
    print(f"Avg tokens per successful run: {avg_tokens_nonzero/1e3:.1f}K")

# ============================================================
# 4. TIME/RESOURCE vs SCORE ANALYSIS
# ============================================================
print("\n" + "="*60)
print("4. TIME/RESOURCE vs SCORE ANALYSIS")
print("="*60)

# Duration analysis
durations = []
for r in runs:
    if r.get("started_at") and r.get("completed_at"):
        dur_min = (r["completed_at"] - r["started_at"]) / 60000
        if 0 < dur_min < 600:  # filter outliers
            durations.append((dur_min, r["score_cont"], r["score_binarized"]))

if durations:
    # Bucket by duration
    buckets = defaultdict(list)
    for dur, score_c, score_b in durations:
        if dur < 30:
            buckets["<30min"].append(score_b)
        elif dur < 60:
            buckets["30-60min"].append(score_b)
        elif dur < 120:
            buckets["1-2h"].append(score_b)
        else:
            buckets[">2h"].append(score_b)

    print("\nSuccess rate by run duration:")
    for bucket in ["<30min", "30-60min", "1-2h", ">2h"]:
        if bucket in buckets:
            scores = buckets[bucket]
            success = sum(scores) / len(scores)
            print(f"  {bucket}: {success*100:.1f}% success ({len(scores)} runs)")

# ============================================================
# 5. TASK DIFFICULTY vs FAILURE RATE
# ============================================================
print("\n" + "="*60)
print("5. TASK DIFFICULTY vs FAILURE RATE")
print("="*60)

# Group by task_family, compute success rate
task_stats = defaultdict(lambda: {"total": 0, "success": 0, "human_minutes": None})
for r in runs:
    tf = r["task_family"]
    task_stats[tf]["total"] += 1
    if r["score_binarized"] > 0:
        task_stats[tf]["success"] += 1
    if r.get("human_minutes") and r["human_minutes"] > 0:
        task_stats[tf]["human_minutes"] = r["human_minutes"]

# Sort by success rate
sorted_tasks = sorted(task_stats.items(), key=lambda x: x[1]["success"]/max(x[1]["total"],1))
print(f"\nTask families sorted by agent success rate:")
print(f"{'Task Family':<40} {'Success Rate':>12} {'Runs':>6} {'Human Min':>10}")
print("-" * 72)
for tf, stats in sorted_tasks[:20]:
    rate = stats["success"] / stats["total"] * 100
    hm = f"{stats['human_minutes']:.0f}" if stats["human_minutes"] else "N/A"
    print(f"{tf:<40} {rate:>10.1f}% {stats['total']:>6} {hm:>10}")

print(f"\n... and {len(sorted_tasks) - 20} more task families")

# RE-Bench specific
print("\n\n--- RE-Bench Tasks ---")
rebench_runs = [r for r in runs if r["task_source"] == "RE-Bench"]
if rebench_runs:
    rb_tasks = defaultdict(lambda: {"total": 0, "success": 0, "scores": []})
    for r in rebench_runs:
        tf = r["task_id"]
        rb_tasks[tf]["total"] += 1
        rb_tasks[tf]["scores"].append(r["score_cont"])
        if r["score_binarized"] > 0:
            rb_tasks[tf]["success"] += 1

    for tf, stats in sorted(rb_tasks.items()):
        rate = stats["success"] / stats["total"] * 100
        avg = statistics.mean(stats["scores"])
        print(f"  {tf}: {rate:.0f}% success ({stats['success']}/{stats['total']}), avg_score={avg:.3f}")

# ============================================================
# 6. KEY METRICS FOR ARA PAPER
# ============================================================
print("\n" + "="*60)
print("6. KEY METRICS FOR ARA PAPER")
print("="*60)

# Compute "exploration waste" - what fraction of total compute goes to dead ends
print(f"\n--- Exploration Waste ---")
print(f"Failed runs: {zero_score}/{total} = {zero_score/total*100:.1f}% of all runs")
print(f"Tokens wasted on failures: {zero_tokens/total_tokens*100:.1f}% of all tokens")
if total_cost > 0:
    print(f"Cost wasted on failures: {zero_cost/total_cost*100:.1f}% of all cost")

# How many UNIQUE solutions do successful runs converge on?
# (approximation: cluster by task_id + model)
success_patterns = defaultdict(int)
for r in nonzero_runs:
    key = (r["task_id"], r["alias"])
    success_patterns[key] += 1

# Multi-attempt tasks: same model, same task, multiple runs
multi_attempt = {k: v for k, v in success_patterns.items() if v > 1}
print(f"\n--- Redundant Exploration ---")
print(f"Unique (task, model) pairs with >1 successful run: {len(multi_attempt)}")
if multi_attempt:
    total_multi = sum(multi_attempt.values())
    print(f"Total runs in those pairs: {total_multi} (redundant: {total_multi - len(multi_attempt)})")

# Score variance within same task
print(f"\n--- Score Variance (same task, different models) ---")
task_scores = defaultdict(list)
for r in runs:
    task_scores[r["task_family"]].append(r["score_cont"])

high_var_tasks = []
for tf, scores in task_scores.items():
    if len(scores) >= 10:
        var = statistics.variance(scores) if len(scores) > 1 else 0
        high_var_tasks.append((tf, var, len(scores), statistics.mean(scores)))

high_var_tasks.sort(key=lambda x: -x[1])
print(f"\nHighest variance tasks (most unpredictable):")
for tf, var, n, mean in high_var_tasks[:10]:
    print(f"  {tf}: var={var:.4f}, mean={mean:.3f}, n={n}")

# ============================================================
# 7. HUMAN vs AGENT COMPARISON
# ============================================================
print("\n" + "="*60)
print("7. HUMAN vs AGENT COMPARISON")
print("="*60)

# Tasks where human_minutes is available
human_data = [(r["task_family"], r["human_minutes"], r["score_binarized"])
              for r in runs if r.get("human_minutes") and r["human_minutes"] > 0]

if human_data:
    # Group by difficulty bucket
    easy = [r for r in runs if r.get("human_minutes") and 0 < r["human_minutes"] <= 60]
    medium = [r for r in runs if r.get("human_minutes") and 60 < r["human_minutes"] <= 480]
    hard = [r for r in runs if r.get("human_minutes") and r["human_minutes"] > 480]

    for label, bucket in [("Easy (<1h human)", easy), ("Medium (1-8h human)", medium), ("Hard (>8h human)", hard)]:
        if bucket:
            success = sum(r["score_binarized"] for r in bucket) / len(bucket)
            print(f"  {label}: {success*100:.1f}% agent success ({len(bucket)} runs)")

# Save summary
summary = {
    "total_runs": total,
    "failure_rate": zero_score / total,
    "tokens_wasted_on_failures_pct": zero_tokens / total_tokens if total_tokens > 0 else None,
    "cost_wasted_on_failures_pct": zero_cost / total_cost if total_cost > 0 else None,
    "total_tokens_M": total_tokens / 1e6,
    "total_cost_usd": total_cost,
    "by_source": {
        source: {
            "runs": len([r for r in runs if r["task_source"] == source]),
            "failure_rate": sum(1 for r in runs if r["task_source"] == source and r["score_binarized"] == 0) / max(1, len([r for r in runs if r["task_source"] == source]))
        }
        for source in task_sources
    },
    "top_models": {
        model: {
            "runs": count,
            "failure_rate": sum(1 for r in runs if r["alias"] == model and r["score_binarized"] == 0) / count,
            "avg_score": statistics.mean(r["score_cont"] for r in runs if r["alias"] == model)
        }
        for model, count in models.most_common(10)
    }
}

out_path = os.path.join(OUT_DIR, "runs_analysis_summary.json")
with open(out_path, "w") as f:
    json.dump(summary, f, indent=2)
print(f"\nSaved summary to {out_path}")
